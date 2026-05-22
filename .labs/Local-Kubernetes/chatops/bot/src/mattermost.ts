import WebSocket from "ws";
// Mattermost client expects global WebSocket
(global as any).WebSocket = WebSocket;

import { Client4 } from "@mattermost/client";
import type { ClaudeAgent } from "./claude";
import type { Config } from "./config";

export class MattermostBot {
  private client: Client4;
  private ws: WebSocket | null = null;
  private agent: ClaudeAgent;
  private config: Config;
  private botUserId: string = "";
  private processing = new Set<string>(); // prevent duplicate processing

  constructor(config: Config, agent: ClaudeAgent) {
    this.config = config;
    this.agent = agent;
    this.client = new Client4();
    this.client.setUrl(config.mattermostUrl);
    this.client.setToken(config.botToken);
  }

  async connect(): Promise<void> {
    // Get bot's own user ID
    const me = await this.client.getMe();
    this.botUserId = me.id;
    console.log(`[mm] Bot user: @${me.username} (${me.id})`);

    // Connect WebSocket
    const wsUrl = this.config.mattermostUrl
      .replace("http://", "ws://")
      .replace("https://", "wss://");

    await this.connectWebSocket(`${wsUrl}/api/v4/websocket`);
  }

  private async connectWebSocket(url: string): Promise<void> {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(url);

      this.ws.on("open", () => {
        // Authenticate
        this.ws!.send(
          JSON.stringify({
            seq: 1,
            action: "authentication_challenge",
            data: { token: this.config.botToken },
          })
        );
        console.log("[mm] WebSocket connected");
        resolve();
      });

      this.ws.on("message", (data: WebSocket.Data) => {
        this.handleWsMessage(data.toString());
      });

      this.ws.on("close", () => {
        console.log("[mm] WebSocket closed, reconnecting in 5s...");
        setTimeout(() => this.connectWebSocket(url), 5000);
      });

      this.ws.on("error", (err) => {
        console.error("[mm] WebSocket error:", err.message);
        reject(err);
      });
    });
  }

  private async handleWsMessage(raw: string): Promise<void> {
    let event: any;
    try {
      event = JSON.parse(raw);
    } catch {
      return;
    }

    if (event.event !== "posted") return;

    const post = JSON.parse(event.data?.post || "{}");

    // Ignore own messages
    if (post.user_id === this.botUserId) return;

    // Check for @mention
    const mention = `@${this.config.botUsername}`;
    if (!post.message?.includes(mention)) return;

    // Prevent duplicate processing
    if (this.processing.has(post.id)) return;
    this.processing.add(post.id);

    // Strip the @mention and process
    const question = post.message.replace(new RegExp(mention, "g"), "").trim();
    if (!question) return;

    console.log(`[mm] @mention from ${post.user_id}: ${question.slice(0, 100)}`);

    try {
      const response = await this.agent.processMessage(question);
      await this.replyToPost(post.channel_id, post.id, response);
    } catch (err) {
      const errMsg =
        err instanceof Error ? err.message : "Unknown error";
      console.error("[mm] Error processing message:", errMsg);
      await this.replyToPost(
        post.channel_id,
        post.id,
        `❌ Error: ${errMsg}`
      );
    } finally {
      this.processing.delete(post.id);
    }
  }

  private async replyToPost(
    channelId: string,
    rootId: string,
    message: string
  ): Promise<void> {
    // Mattermost has a 16383 char limit per post
    const maxLen = 16000;
    if (message.length > maxLen) {
      message = message.slice(0, maxLen) + "\n\n...(truncated)";
    }

    await this.client.createPost({
      channel_id: channelId,
      root_id: rootId,
      message,
    } as any);
  }

  async postToChannel(channelName: string, teamName: string, message: string): Promise<void> {
    try {
      const team = await this.client.getTeamByName(teamName);
      const channel = await this.client.getChannelByName(team.id, channelName);

      const maxLen = 16000;
      const truncated =
        message.length > maxLen
          ? message.slice(0, maxLen) + "\n\n...(truncated)"
          : message;

      await this.client.createPost({
        channel_id: channel.id,
        message: truncated,
      } as any);
    } catch (err) {
      console.error(`[mm] Failed to post to #${channelName}:`, err);
    }
  }

  close(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}
