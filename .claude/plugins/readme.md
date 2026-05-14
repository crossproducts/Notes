# Plugins

Plugins connect Claude to external tools and data sources via the **Model Context Protocol (MCP)**. MCP servers expose resources, tools, and prompts that Claude can use during a session.

## What Belongs Here

MCP server configuration files and any related manifests or documentation for plugins used in this project.

## Configuration

MCP servers are registered in `.claude/settings.json` under `mcpServers`:

```json
{
  "mcpServers": {
    "<server-name>": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/<package>"],
      "env": {
        "API_KEY": "${MY_API_KEY}"
      }
    }
  }
}
```

## Transport Types

| Type | Description |
|------|-------------|
| `stdio` | Local process, communicates via stdin/stdout (default) |
| `sse` | Remote server via HTTP Server-Sent Events |

## Common MCP Servers

| Server | Package | What It Provides |
|--------|---------|------------------|
| Filesystem | `@modelcontextprotocol/server-filesystem` | Read/write local files |
| GitHub | `@modelcontextprotocol/server-github` | Repos, PRs, issues |
| Kubernetes | `mcp-server-kubernetes` | Cluster resources |
| PostgreSQL | `@modelcontextprotocol/server-postgres` | Database queries |
| Brave Search | `@modelcontextprotocol/server-brave-search` | Web search |

## File Naming

Document each plugin with a matching file:
- `github.md` — GitHub MCP setup and usage notes
- `kubernetes.md` — K8s MCP setup and usage notes