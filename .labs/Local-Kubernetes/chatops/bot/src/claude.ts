import Anthropic from "@anthropic-ai/sdk";
import type { Tool } from "@modelcontextprotocol/sdk/types.js";
import type { McpKubernetesClient } from "./mcp-client";
import type { Config } from "./config";

const SYSTEM_PROMPT = `You are a Kubernetes operations assistant running inside a ChatOps bot.
You have access to tools that query a live Kubernetes cluster.

Guidelines:
- Be concise. Users are reading this in a chat window.
- Use bullet points and short summaries, not paragraphs.
- When reporting pod status, group by namespace and highlight issues (CrashLoopBackOff, OOMKilled, Pending, etc).
- For health checks, lead with a status line: ✅ Healthy, ⚠️ Warnings, or ❌ Issues Found.
- If something is wrong, suggest a next step (check logs, describe pod, etc).
- Format output for Mattermost markdown (supports tables, code blocks, bold).`;

interface ClaudeTool {
  name: string;
  description: string;
  input_schema: Record<string, unknown>;
}

function convertMcpToolsToClaude(mcpTools: Tool[]): ClaudeTool[] {
  return mcpTools.map((t) => ({
    name: t.name,
    description: t.description || "",
    input_schema: t.inputSchema as Record<string, unknown>,
  }));
}

export class ClaudeAgent {
  private anthropic: Anthropic;
  private mcpClient: McpKubernetesClient;
  private model: string;

  constructor(config: Config, mcpClient: McpKubernetesClient) {
    this.anthropic = new Anthropic({ apiKey: config.anthropicApiKey });
    this.mcpClient = mcpClient;
    this.model = config.claudeModel;
  }

  async processMessage(userMessage: string): Promise<string> {
    const tools = convertMcpToolsToClaude(this.mcpClient.getTools());

    const messages: Anthropic.MessageParam[] = [
      { role: "user", content: userMessage },
    ];

    // Agentic tool-use loop
    let maxIterations = 10;
    while (maxIterations-- > 0) {
      const response = await this.anthropic.messages.create({
        model: this.model,
        max_tokens: 4096,
        system: SYSTEM_PROMPT,
        tools: tools as Anthropic.Tool[],
        messages,
      });

      // If no tool use, extract text and return
      if (response.stop_reason === "end_turn") {
        return this.extractText(response.content);
      }

      // Process tool calls
      if (response.stop_reason === "tool_use") {
        // Add assistant response to messages
        messages.push({ role: "assistant", content: response.content });

        // Execute each tool call via MCP
        const toolResults: Anthropic.ToolResultBlockParam[] = [];
        for (const block of response.content) {
          if (block.type === "tool_use") {
            try {
              const result = await this.mcpClient.callTool(
                block.name,
                block.input as Record<string, unknown>
              );

              // Extract text content from MCP result
              const content = result.content
                .map((c: { type: string; text?: string }) =>
                  c.type === "text" ? c.text : JSON.stringify(c)
                )
                .join("\n");

              // Truncate very large responses
              const truncated =
                content.length > 50000
                  ? content.slice(0, 50000) + "\n...(truncated)"
                  : content;

              toolResults.push({
                type: "tool_result",
                tool_use_id: block.id,
                content: truncated,
              });
            } catch (err) {
              toolResults.push({
                type: "tool_result",
                tool_use_id: block.id,
                content: `Error: ${err instanceof Error ? err.message : String(err)}`,
                is_error: true,
              });
            }
          }
        }

        // Feed results back to Claude
        messages.push({ role: "user", content: toolResults });
        continue;
      }

      // Unknown stop reason, return what we have
      return this.extractText(response.content);
    }

    return "⚠️ Reached maximum tool call iterations. Partial results may be above.";
  }

  private extractText(content: Anthropic.ContentBlock[]): string {
    return content
      .filter((b): b is Anthropic.TextBlock => b.type === "text")
      .map((b) => b.text)
      .join("\n");
  }
}
