# draw.io plugin — `notes-arch`

A custom draw.io plugin for this repo. It adds one palette, **Notes / Architecture**,
pinned to the top of the shape sidebar, and sets the default styles so shapes you draw
by hand match the ones you drag in.

- Plugin: [`Architecture/Diagrams/drawio-plugins/notes-arch.js`](drawio-plugins/notes-arch.js)
- Wiring: [`.vscode/settings.json`](../../.vscode/settings.json)
- Editor: the `hediet.vscode-drawio` VS Code extension (already installed)

## First run

The extension refuses to execute a plugin until you approve it. On the first
`.drawio` file you open after this change, VS Code prompts with the plugin's
fingerprint — choose **Allow**. Edit the plugin and you will be prompted again,
because the fingerprint changes. If you miss the prompt, run
`Developer: Reload Window` and reopen the file.

## What is in the palette

| Group | Shapes | Color |
|---|---|---|
| Entry / edge | Client, API Gateway, mTLS Edge, Load Balancer | blue |
| Compute | Service, Function, Job, Pod (container) | green |
| Data | Database, Cache, Object Store, Data Lake | amber |
| Async | Queue, Topic, Stream | purple |
| AI | LLM, Agent, Vector DB, MCP Server | teal |
| Ops | Metrics, Logs, Traces, CI/CD, Secrets | grey |
| Boundaries | VPC, Trust Boundary, Cluster (containers) | outline only |
| Edges | sync, async, mTLS, telemetry | per-type stroke |

Every shape carries search tags, so the sidebar search box finds them by the terms
used in these notes (`eks`, `rag`, `otel`, `zero trust`, …) rather than only by label.

`Pod`, `VPC`, `Trust Boundary` and `Cluster` are draw.io *containers* — drop other
shapes inside and they move with the boundary.

## Conventions

- **Save as `.drawio.svg`**, not `.drawio`. The file is a valid SVG that GitHub renders
  inline, and it still opens as an editable diagram in VS Code. Reference it from a
  note with a plain image link.
- Keep the color meaning above consistent across diagrams — the color is the type,
  the label is the instance.
- Mermaid stays the default for small sequence/flow diagrams (see [readme](readme.md));
  reach for draw.io when the layout itself carries meaning (zones, nesting, topology).

## Editing the plugin

It is plain JavaScript using the draw.io plugin API — `Draw.loadPlugin(ui => …)`,
`ui.sidebar.createVertexTemplateEntry(style, w, h, label, title, null, null, tags)`.
Shape styles are the same strings you get from **Edit Style** (`Ctrl+E`) on a selected
shape, so the fastest way to add an entry is: draw it, style it, `Ctrl+E`, copy the
string into the `vertices` array.

After editing, reload the window and re-approve the new fingerprint.
