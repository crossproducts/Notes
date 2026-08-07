"""
Holmes pipe function for Open WebUI.

Calls the Holmes /api/chat endpoint directly (SSE streaming), bypassing
the former ag-ui-bridge / nginx-shim chain.

Install / update: ./install-pipe.sh (idempotent)
Re-install after wiping openwebui-data volume: ./install-pipe.sh
"""

import json
import asyncio
from typing import AsyncGenerator, Optional
from pydantic import BaseModel


# In-process state: chat_id -> conversation_history from the last ai_answer_end.
# Survives Open WebUI container restarts only if the pipe module stays loaded
# (i.e. it's reset whenever the container restarts). Falls back gracefully.
_history_store: dict[str, list[dict]] = {}


class Pipe:
    class Valves(BaseModel):
        HOLMES_URL: str = "http://holmes:5050"
        TIMEOUT: int = 600  # seconds; Holmes investigations can be slow

    def __init__(self):
        self.valves = self.Valves()

    def pipes(self) -> list[dict]:
        """Advertise one model entry in Open WebUI's model list."""
        return [{"id": "holmes", "name": "Holmes (SRE)"}]

    async def pipe(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __request__=None,
        __event_emitter__=None,
        __metadata__: Optional[dict] = None,
    ) -> AsyncGenerator[str, None]:
        import httpx

        messages: list[dict] = body.get("messages", [])
        if not messages:
            yield "Error: no messages in request body."
            return

        # Last user message is the question for Holmes.
        ask: str = messages[-1].get("content", "")
        if not ask:
            yield "Error: last message has no content."
            return

        # Multi-turn: try to reuse Holmes's native conversation_history.
        chat_id: Optional[str] = (__metadata__ or {}).get("chat_id")
        conversation_history: Optional[list[dict]] = None

        if chat_id and chat_id in _history_store:
            conversation_history = _history_store[chat_id]
        elif len(messages) > 1:
            # We have prior turns but no stored history (e.g. container restart).
            # Build a compact summary prefix so Holmes has some context.
            prior = messages[:-1]
            summary_parts = []
            for m in prior:
                role = m.get("role", "user")
                content = m.get("content", "")
                if content:
                    # Truncate each prior message to 300 chars to avoid ballooning the ask.
                    snippet = content[:300] + ("…" if len(content) > 300 else "")
                    summary_parts.append(f"[{role}]: {snippet}")
            if summary_parts:
                prior_text = "\n".join(summary_parts)
                ask = f"Previous conversation:\n{prior_text}\n\nCurrent question: {ask}"
            # conversation_history stays None so Holmes builds its own system prompt.

        payload = {
            "ask": ask,
            "stream": True,
            "conversation_history": conversation_history,
        }

        url = f"{self.valves.HOLMES_URL}/api/chat"

        async def emit_status(msg: str) -> None:
            if __event_emitter__:
                await __event_emitter__(
                    {"type": "status", "data": {"description": msg, "done": False}}
                )

        async def emit_status_done(msg: str) -> None:
            if __event_emitter__:
                await __event_emitter__(
                    {"type": "status", "data": {"description": msg, "done": True}}
                )

        try:
            async with httpx.AsyncClient(timeout=self.valves.TIMEOUT) as client:
                async with client.stream("POST", url, json=payload) as resp:
                    if resp.status_code != 200:
                        body_text = await resp.aread()
                        yield f"Holmes error {resp.status_code}: {body_text.decode()}"
                        return

                    # Parse SSE: lines look like "data: <json>" or "event: <name>"
                    event_type: str = ""
                    # Track whether any ai_message chunks were yielded; if not, fall
                    # back to the analysis field in ai_answer_end (Holmes omits streaming
                    # ai_message events for short/non-tool answers).
                    streamed_any_text: bool = False
                    async for raw_line in resp.aiter_lines():
                        line = raw_line.strip()
                        if not line:
                            event_type = ""
                            continue

                        if line.startswith("event:"):
                            event_type = line[len("event:"):].strip()
                            continue

                        if not line.startswith("data:"):
                            continue

                        data_str = line[len("data:"):].strip()

                        # Holmes sends: "data: <json>" with event type in "event:" line.
                        try:
                            data = json.loads(data_str)
                        except json.JSONDecodeError:
                            # Plain text delta — unlikely from Holmes but handle it.
                            yield data_str
                            streamed_any_text = True
                            continue

                        etype = event_type or data.get("type", "")

                        if etype == "ai_message":
                            chunk = data.get("content", data.get("message", ""))
                            if chunk:
                                yield chunk
                                streamed_any_text = True

                        elif etype == "start_tool_calling":
                            tool_name = data.get("tool_name", data.get("name", "tool"))
                            tool_input = data.get("input", "")
                            label = f"Running {tool_name}"
                            if tool_input:
                                label += f": {str(tool_input)[:120]}"
                            await emit_status(label)

                        elif etype == "tool_calling_result":
                            tool_name = data.get("tool_name", data.get("name", "tool"))
                            await emit_status(f"Got result from {tool_name}")

                        elif etype == "ai_answer_end":
                            # Holmes hands back the full conversation_history for round-tripping.
                            new_history = data.get("conversation_history")
                            if new_history and chat_id:
                                _history_store[chat_id] = new_history
                            # Fallback: for short answers Holmes doesn't emit ai_message SSE
                            # events — the answer is only in the analysis field here.
                            if not streamed_any_text:
                                analysis = data.get("analysis", "")
                                if analysis:
                                    yield analysis
                            await emit_status_done("Investigation complete")

                        elif etype == "token_count":
                            # Informational — ignore silently.
                            pass

                        elif etype == "error":
                            err_msg = data.get("message", data.get("error", str(data)))
                            yield f"\n\nHolmes error: {err_msg}"
                            await emit_status_done(f"Error: {err_msg}")

                        elif etype == "approval_required":
                            msg = data.get("message", "Holmes requires approval to proceed.")
                            yield f"\n\n**Approval required:** {msg}"
                            await emit_status_done("Waiting for approval")

        except httpx.ConnectError:
            yield (
                f"Cannot connect to Holmes at {self.valves.HOLMES_URL}. "
                "Is the `holmes` service running?"
            )
        except httpx.TimeoutException:
            yield (
                f"Holmes did not respond within {self.valves.TIMEOUT}s. "
                "Consider increasing the TIMEOUT valve."
            )
        except Exception as exc:
            yield f"Pipe error: {type(exc).__name__}: {exc}"
