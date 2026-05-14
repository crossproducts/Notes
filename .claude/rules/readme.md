# Rules

Rule files define project-specific constraints, standards, and guidelines that Claude must follow. They supplement the high-level instructions in `CLAUDE.md` with granular, domain-specific rules.

## What Belongs Here

Detailed rules organized by concern. Claude reads these when referenced from `CLAUDE.md` or a command.

## File Naming

Organize by domain:
- `coding-standards.md` — language style, formatting, naming conventions
- `security.md` — secrets handling, auth patterns, what never to do
- `testing.md` — test coverage requirements, frameworks, naming
- `git.md` — branch naming, commit message format, PR rules
- `architecture.md` — design patterns, layer boundaries, dependencies
- `documentation.md` — docstring format, README standards

## Rule File Template

```markdown
# Rules: <Domain>

## Always
- <Rule that must always be followed>

## Never
- <Rule that must never be violated>

## Prefer
- <Soft preference or best practice>

## Examples
<Concrete good/bad examples if helpful>
```

## How to Reference Rules

In `CLAUDE.md`:
```
Follow the rules in:
- @.claude/rules/coding-standards.md
- @.claude/rules/security.md
```

In a command file:
```
Before writing any code, review @.claude/rules/coding-standards.md
```

## Tips

- Keep rules **specific and actionable** — avoid vague guidelines
- Use **Always / Never / Prefer** structure for clarity
- Rules here override general Claude defaults for this project