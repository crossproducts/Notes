import { loadConfig } from "./config";
import { McpKubernetesClient } from "./mcp-client";
import { ClaudeAgent } from "./claude";
import { MattermostBot } from "./mattermost";
import { HealthCheckScheduler } from "./health-check";

async function main() {
  console.log("=== ChatOps Bot Starting ===");

  // 1. Load configuration
  const config = loadConfig();
  console.log(`[config] Mattermost: ${config.mattermostUrl}`);
  console.log(`[config] Model: ${config.claudeModel}`);
  console.log(`[config] Kubeconfig: ${config.kubeconfig}`);

  // 2. Initialize MCP client (connect to kubernetes-mcp-server)
  const mcpClient = new McpKubernetesClient(config.kubeconfig);
  await mcpClient.connect();
  console.log(`[init] MCP client ready (${mcpClient.getTools().length} tools)`);

  // 3. Initialize Claude agent
  const agent = new ClaudeAgent(config, mcpClient);
  console.log("[init] Claude agent ready");

  // 4. Connect to Mattermost
  const bot = new MattermostBot(config, agent);
  await bot.connect();
  console.log("[init] Mattermost bot connected");

  // 5. Start health check scheduler
  const healthCheck = new HealthCheckScheduler(config, agent, bot);
  healthCheck.start();

  console.log("=== ChatOps Bot Ready ===");
  console.log(`  @${config.botUsername} is listening for mentions`);

  // Graceful shutdown
  const shutdown = async () => {
    console.log("\n[shutdown] Stopping...");
    healthCheck.stop();
    bot.close();
    await mcpClient.close();
    process.exit(0);
  };

  process.on("SIGTERM", shutdown);
  process.on("SIGINT", shutdown);
}

main().catch((err) => {
  console.error("Fatal error:", err);
  process.exit(1);
});
