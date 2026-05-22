export interface Config {
  mattermostUrl: string;
  botToken: string;
  botUsername: string;
  anthropicApiKey: string;
  claudeModel: string;
  kubeconfig: string;
  healthCheckIntervalMs: number;
  healthCheckChannel: string;
}

export function loadConfig(): Config {
  const required = (key: string): string => {
    const val = process.env[key];
    if (!val) throw new Error(`Missing required env var: ${key}`);
    return val;
  };

  return {
    mattermostUrl: process.env.MATTERMOST_URL || "http://mattermost:8065",
    botToken: required("BOT_TOKEN"),
    botUsername: process.env.BOT_USERNAME || "k8s-bot",
    anthropicApiKey: required("ANTHROPIC_API_KEY"),
    claudeModel: process.env.CLAUDE_MODEL || "claude-sonnet-4-20250514",
    kubeconfig: process.env.KUBECONFIG || "/home/node/.kube/config",
    healthCheckIntervalMs: parseInt(process.env.HEALTH_CHECK_INTERVAL_MS || "300000", 10),
    healthCheckChannel: process.env.HEALTH_CHECK_CHANNEL || "k8s-alerts",
  };
}
