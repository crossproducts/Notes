# Docusaurus

Docusaurus is an open-source static site generator built by Meta, designed for building documentation websites quickly and easily.

## Key Features

- **MDX Support** – Write documentation in Markdown with embedded React components (MDX).
- **Versioning** – Maintain multiple versions of your documentation with built-in versioning support.
- **Search** – Integrated Algolia DocSearch support for full-text search.
- **Theming** – Fully customizable themes with React; dark/light mode out of the box.
- **i18n** – Built-in internationalization (i18n) for multi-language documentation sites.
- **Blog** – Includes a blog plugin for publishing posts alongside your docs.

## Installation

```bash
npx create-docusaurus@latest my-website classic
cd my-website
npm start
```

## Project Structure

```
my-website/
├── blog/           # Blog posts
├── docs/           # Documentation markdown files
├── src/
│   ├── components/ # Custom React components
│   ├── css/        # Global styles
│   └── pages/      # Custom standalone pages
├── static/         # Static assets (images, etc.)
├── docusaurus.config.js  # Main configuration file
└── sidebars.js     # Sidebar navigation configuration
```

## Common Commands

| Command | Description |
|---|---|
| `npm start` | Start the local dev server |
| `npm run build` | Build the production site |
| `npm run serve` | Serve the built site locally |
| `npm run deploy` | Deploy to GitHub Pages |

## Configuration (`docusaurus.config.js`)

Key fields in the config file:

- `title` – Site title
- `url` – Your site's URL
- `baseUrl` – Base URL path
- `organizationName` – GitHub org/user (for deployment)
- `projectName` – GitHub repo name (for deployment)
- `presets` – Configure docs, blog, and theme plugins
- `themeConfig` – Navbar, footer, and color mode settings

## Useful Links

- [Official Docs](https://docusaurus.io/docs)
- [GitHub Repository](https://github.com/facebook/docusaurus)
- [Deployment Guide](https://docusaurus.io/docs/deployment)
