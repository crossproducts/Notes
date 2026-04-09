from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import httpx
import json

OLLAMA_BASE_URL = "http://localhost:11434"

app = FastAPI(title="Ollama Inference API")


class ChatRequest(BaseModel):
    model: str
    prompt: str
    stream: bool = False
    system: str | None = None
    temperature: float | None = None


class GenerateRequest(BaseModel):
    model: str
    prompt: str
    stream: bool = False
    system: str | None = None
    temperature: float | None = None


@app.get("/models")
async def list_models():
    """List all locally available Ollama models."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            response.raise_for_status()
            return response.json()
        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail="Ollama is not running. Start it with: ollama serve")


@app.post("/generate")
async def generate(req: GenerateRequest):
    """Single-turn text generation (raw completion)."""
    payload = {"model": req.model, "prompt": req.prompt, "stream": req.stream}
    if req.system:
        payload["system"] = req.system
    if req.temperature is not None:
        payload["options"] = {"temperature": req.temperature}

    async with httpx.AsyncClient(timeout=120) as client:
        try:
            if req.stream:
                return StreamingResponse(
                    _stream_ollama(client, f"{OLLAMA_BASE_URL}/api/generate", payload),
                    media_type="text/event-stream",
                )
            response = await client.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail="Ollama is not running. Start it with: ollama serve")


@app.post("/chat")
async def chat(req: ChatRequest):
    """Multi-turn chat completion using Ollama's chat endpoint."""
    messages = []
    if req.system:
        messages.append({"role": "system", "content": req.system})
    messages.append({"role": "user", "content": req.prompt})

    payload = {"model": req.model, "messages": messages, "stream": req.stream}
    if req.temperature is not None:
        payload["options"] = {"temperature": req.temperature}

    async with httpx.AsyncClient(timeout=120) as client:
        try:
            if req.stream:
                return StreamingResponse(
                    _stream_ollama(client, f"{OLLAMA_BASE_URL}/api/chat", payload),
                    media_type="text/event-stream",
                )
            response = await client.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail="Ollama is not running. Start it with: ollama serve")


async def _stream_ollama(client: httpx.AsyncClient, url: str, payload: dict):
    """Yield SSE lines from Ollama's streaming response."""
    async with client.stream("POST", url, json=payload, timeout=120) as response:
        response.raise_for_status()
        async for line in response.aiter_lines():
            if line:
                yield f"data: {line}\n\n"
