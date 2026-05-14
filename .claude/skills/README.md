# Skills

Skill files are reusable prompt modules that give Claude a specific capability or area of expertise. They can be composed into commands, referenced from `CLAUDE.md`, or invoked inline.

## What Belongs Here

Focused, reusable instructional prompts for a specific skill or domain. Think of them as "prompt libraries" — chunks of expertise you can mix and match.

## File Naming

Name files by the skill or domain:
- `bash-scripting.md` — Shell scripting best practices and patterns
- `kubernetes.md` — K8s resource authoring and troubleshooting
- `code-review.md` — How to perform a thorough code review
- `technical-writing.md` — How to write clear documentation
- `sql.md` — Query writing, optimization, schema design
- `python.md` — Pythonic patterns, type hints, packaging

## Skill File Template

```markdown
# Skill: <Name>

## Purpose
<What this skill enables Claude to do better>

## Core Concepts
<Key knowledge or mental models for this domain>

## Patterns & Best Practices
<Concrete do's and don'ts>

## Examples
<Worked examples or templates>

## Common Pitfalls
<Things to watch out for>
```

## How to Use Skills

Reference directly in a command:
```
Using the expertise in @.claude/skills/code-review.md, review the following PR...
```

Reference in `CLAUDE.md` to always apply:
```
Apply the patterns in @.claude/skills/python.md when writing Python code.
```

Compose multiple skills:
```
Using @.claude/skills/kubernetes.md and @.claude/skills/bash-scripting.md,
write a deployment health-check script.
```