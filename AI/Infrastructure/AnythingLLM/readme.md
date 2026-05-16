# AnythingLLM

> [!NOTE]
> **Status**: Pending

---

> Open-source, self-hosted LLM application platform that lets you chat with documents using any LLM.

## Overview

| Property | Detail |
|---|---|
| Type | Self-Hosted LLM Platform |
| Interface | Web UI + Desktop App |
| Platforms | Docker, macOS, Windows, Linux |
| Website | https://anythingllm.com |
| GitHub | https://github.com/Mintplex-Labs/anything-llm |

## Key Features

- Chat with documents (PDF, DOCX, CSV, TXT, etc.)
- Supports multiple LLM providers (OpenAI, Ollama, Anthropic, etc.)
- Multi-user support with role-based access
- Workspaces for isolated document collections
- Agent support and web scraping
- Embedding and vector database integrations

## Installation

### Docker
```bash
docker pull mintplexlabs/anythingllm
docker run -d -p 3001:3001 \
  -v ${PWD}/anythingllm:/app/server/storage \
    mintplexlabs/anythingllm
    ```

    ### Desktop App
    ```
    Download from https://anythingllm.com/download
    ```

    ## Getting Started

    1. Start the app (Docker or Desktop)
    2. Navigate to http://localhost:3001
    3. Configure your LLM provider (API key or local Ollama)
    4. Create a workspace
    5. Upload documents and start chatting
    