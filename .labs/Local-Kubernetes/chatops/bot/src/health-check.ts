import type { ClaudeAgent } from "./claude";
import type { MattermostBot } from "./mattermost";
import type { Config } from "./config";

const HEALTH_CHECK_PROMPT = `Give a brief health summary of the Kubernetes cluster. Check:
- Node status and resource utilization
- Pod health across all namespaces (highlight any not Running/Ready)
- Recent warning or error events (last 15 minutes)
- Any pods in CrashLoopBackOff, ImagePullBackOff, or Pending state

Format as a concise Mattermost post with a status line at the top.`;

export class HealthCheckScheduler {
  private agent: ClaudeAgent;
  private bot: MattermostBot;
  private config: Config;
  private timer: NodeJS.Timeout | null = null;

  constructor(config: Config, agent: ClaudeAgent, bot: MattermostBot) {
    this.config = config;
    this.agent = agent;
    this.bot = bot;
  }

  start(): void {
    if (this.config.healthCheckIntervalMs <= 0) {
      console.log("[health] Disabled (interval <= 0)");
      return;
    }

    console.log(
      `[health] Scheduling checks every ${this.config.healthCheckIntervalMs / 1000}s → #${this.config.healthCheckChannel}`
    );

    // Run first check after a short delay (let things settle)
    setTimeout(() => this.runCheck(), 30000);

    this.timer = setInterval(
      () => this.runCheck(),
      this.config.healthCheckIntervalMs
    );
  }

  async runCheck(): Promise<void> {
    console.log("[health] Running scheduled health check...");
    try {
      const report = await this.agent.processMessage(HEALTH_CHECK_PROMPT);
      await this.bot.postToChannel(
        this.config.healthCheckChannel,
        "chatops",
        `### 🔄 Scheduled Health Check\n\n${report}`
      );
      console.log("[health] Posted report to #" + this.config.healthCheckChannel);
    } catch (err) {
      console.error("[health] Check failed:", err);
    }
  }

  stop(): void {
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
  }
}
