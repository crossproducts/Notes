# Hooks

Hooks let you run shell commands automatically at key points in Claude's lifecycle — before or after tool calls, on notifications, or when Claude stops.

## What Belongs Here

Shell scripts (`.sh`) or executable files that hooks reference. Hook configuration lives in `.claude/settings.json` under the `hooks` key.

## Hook Types

| Hook | When It Fires | Can Block? |
|------|--------------|------------|
| `PreToolUse` | Before a tool runs | Yes (exit non-zero) |
| `PostToolUse` | After a tool runs | No |
| `Notification` | When Claude sends a notification | No |
| `Stop` | When Claude finishes responding | No |

## Configuration in settings.json

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/pre-bash.sh"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/post-write.sh"
          }
        ]
      }
    ]
  }
}
```

## Common Use Cases
- **PreToolUse**: Validate inputs, enforce security rules, log tool usage
- **PostToolUse**: Run linters/formatters after file writes, trigger tests after code changes
- **Notification**: Send Slack/Teams alerts when Claude needs input
- **Stop**: Log session summaries, clean up temp files