# Claude Code Flowstate

## `settings.local.json`
```json
{
  "permissions": {
    "defaultMode": "bypassPermissions"
  }
}
```

## `claude-auto-retr`
```bash
npm i -g claude-auto-retry
claude-auto-retry install
```

## `TODO-ai.md`

## `TODO-user.nd`

## Enable Remote Control
```bash
claude /config
/Enable Remote Control for all sessions # true
```

```bash
choco install psmux -y
psmux new-session -s claude "claude /rc"
```
or
```bash
psmux ls
psmux attach claude
```

## Scheduled for Token Window
- Token resets every 5 hours
- Cronjob to start token window
- Apache Airflow to manage cronjobs