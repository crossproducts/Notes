# Commands

Custom slash commands extend Claude Code with project-specific shortcuts. Each `.md` file in this directory becomes a `/command-name` available in Claude Code.

## What Belongs Here

Shortcuts for frequent tasks: code review, generating boilerplate, running checklists, formatting output, etc.

## File Naming

Filename (without `.md`) becomes the slash command.
Examples:
- `review.md` → `/review`
- `standup.md` → `/standup`
- `scaffold.md` → `/scaffold`

## Command File Template

```markdown
# Command: <name>

<Description of what this command does>

## Instructions

<Step-by-step instructions Claude should follow>

## Arguments

$ARGUMENTS — <describe what the user passes in>
```

## Using Arguments

Use `$ARGUMENTS` as a placeholder for user-provided input:

```
/review src/main.py
```

Inside the command file, `$ARGUMENTS` will be replaced with `src/main.py`.

## Namespacing

Subdirectories create namespaced commands:
- `commands/git/commit.md` → `/git:commit`
- `commands/k8s/deploy.md` → `/k8s:deploy`