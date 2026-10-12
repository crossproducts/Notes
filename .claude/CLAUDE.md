# CLAUDE.md

This file is automatically read by Claude Code at the start of every session. It provides project context, conventions, and instructions.

## Project Overview

> Describe your project here: what it does, its architecture, key technologies.

## Local Tools (`.labs/`)

Standalone CLI projects, each with its own README, `.env`, and a Claude **skill**
that loads on-demand when a task matches (see `.claude/skills/`):

- **`.labs/email-sender/`** — sends real email via Gmail SMTP, two-way SMS through
  carrier gateways, and a whitelist-only local-model autoresponder.
  Skill: `email-sender`.
- **`.labs/audio-extraction/`** — reel/video → strategy → backtest pipeline
  (transcribe → interpret → generate → data → backtest → report).
  Skill: `reel-backtest`.
- **`.labs/explainer-video/`** — turns a Python "deck" into a narrated MP4
  (Playwright-rendered slides + local Kokoro-82M TTS + ffmpeg). Model weights
  and rendered output are gitignored; the deck is the source. No skill yet.

## Repository Structure

```
.claude/
├── CLAUDE.md          ← You are here
├── settings.json      ← Shared permissions & tool config
├── settings.local.json← Local overrides (gitignored)
├── agents/            ← Sub-agent definitions
├── commands/          ← Custom slash commands
├── hooks/             ← Lifecycle hooks (pre/post tool)
├── output-styles/     ← Response formatting styles
├── plugins/           ← MCP server configs
├── rules/             ← Project-specific rules
└── skills/            ← Reusable skill prompts
```

## Key Conventions

> Add your project's coding standards, naming conventions, and workflow rules here.
> Or reference rule files:

<!-- 
Follow the rules in:
- @.claude/rules/coding-standards.md
- @.claude/rules/security.md
- @.claude/rules/git.md
-->

## Active Skills

> Reference skill files Claude should always apply:

<!--
- @.claude/skills/python.md
- @.claude/skills/kubernetes.md
-->

## Default Output Style

> Reference an output style for all responses:

<!-- @.claude/output-styles/technical.md -->

## Important Notes

- `settings.json` is committed — changes affect all team members
- `settings.local.json` is gitignored — for personal/local overrides only
- Custom commands are in `.claude/commands/` — run them with `/command-name`
- MCP plugins are configured in `settings.json` under `mcpServers`