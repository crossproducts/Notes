# Output Styles

Output style files define how Claude formats and presents its responses. Reference a style file in a command or in `CLAUDE.md` to shape Claude's communication style for a given context.

## What Belongs Here

Markdown files that describe a formatting persona or presentation standard.

## File Naming

Name files by context or audience:
- `concise.md` — short, direct answers
- `detailed.md` — thorough explanations with examples
- `technical.md` — code-first, minimal prose
- `report.md` — structured document with headers and sections
- `executive.md` — high-level summaries, no jargon

## Style File Template

```markdown
# Style: <name>

## Tone
<Formal / Casual / Technical / Friendly>

## Format
- Use bullet points for lists
- Use headers to separate sections
- Keep responses under X words
- Always include a code example when relevant

## Avoid
- Jargon / Passive voice / Long paragraphs

## Example Output
<Short example of what a response in this style looks like>
```

## How to Apply a Style

In a command file:
```
Respond using the style defined in @.claude/output-styles/technical.md
```

In `CLAUDE.md` (applies globally):
```
Default output style: @.claude/output-styles/concise.md
```