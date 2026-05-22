import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import type { Tool, CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import path from "path";

export class McpKubernetesClient {
  private client: Client;
  private transport: StdioClientTransport | null = null;
  private tools: Tool[] = [];
  private connected = false;
  private kubeconfig: string;

  constructor(kubeconfig: string) {
    this.kubeconfig = kubeconfig;
    this.client = new Client({
      name: "chatops-bot",
      version: "1.0.0",
    });
  }

  async connect(): Promise<void> {
    // Resolve the kubernetes-mcp-server binary from node_modules
    const serverBin = path.resolve(
      __dirname,
      "..",
      "node_modules",
      ".bin",
      "kubernetes-mcp-server"
    );

    this.transport = new StdioClientTransport({
      command: serverBin,
      args: [],
      env: {
        ...process.env,
        KUBECONFIG: this.kubeconfig,
      },
    });

    await this.client.connect(this.transport);
    this.connected = true;
    console.log("[mcp] Connected to kubernetes-mcp-server");

    // Discover available tools
    await this.refreshTools();
  }

  private async refreshTools(): Promise<void> {
    this.tools = [];
    let cursor: string | undefined;

    do {
      const result = await this.client.listTools({ cursor });
      this.tools.push(...result.tools);
      cursor = result.nextCursor;
    } while (cursor);

    console.log(`[mcp] Discovered ${this.tools.length} K8s tools`);
  }

  getTools(): Tool[] {
    return this.tools;
  }

  async callTool(
    name: string,
    args: Record<string, unknown>
  ): Promise<CallToolResult> {
    if (!this.connected) {
      throw new Error("MCP client not connected");
    }

    console.log(`[mcp] Calling tool: ${name}`);
    const result = await this.client.callTool({ name, arguments: args });
    return result as CallToolResult;
  }

  async close(): Promise<void> {
    if (this.connected) {
      await this.client.close();
      this.connected = false;
      console.log("[mcp] Disconnected");
    }
  }

  isConnected(): boolean {
    return this.connected;
  }
}
