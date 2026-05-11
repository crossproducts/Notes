# Open WebUI

> [!NOTE]
> **Status**: Pending

---

> Self-hosted, extensible web interface for LLMs designed to work with Ollama and OpenAI-compatible APIs.

## Overview

| Property | Detail |
|---|---|
| Type | Self-Hosted LLM Web UI |
| Interface | Web UI |
| Platforms | Docker, Kubernetes |
| Website | https://openwebui.com |
| GitHub | https://github.com/open-webui/open-webui |

## Key Features

- Intuitive ChatGPT-style interface for local LLMs
- Native Ollama integration
- OpenAI API compatibility
- Multi-model conversations
- RAG (Retrieval Augmented Generation) support
- Image generation support (AUTOMATIC1111, ComfyUI)
- Multi-user with role-based permissions
- Custom model system prompts and presets
- Markdown and code highlighting

## Installation

### Docker (with Ollama on host)
```bash
docker run -d \
  --network=host \
    -v open-webui:/app/backend/data \
      --name open-webui \
        --restart always \
          ghcr.io/open-webui/open-webui:main
          ```

          ### Docker (with bundled Ollama)
          ```bash
          docker run -d -p 3000:8080 \
            --gpus all \
              -v ollama:/root/.ollama \
                -v open-webui:/app/backend/data \
                  --name open-webui \
                    --restart always \
                      ghcr.io/open-webui/open-webui:ollama
                      ```

                      ## Getting Started

                      1. Start Open WebUI (see Installation)
                      2. Navigate to http://localhost:3000
                      3. Create an admin account on first run
                      4. Connect to Ollama (auto-detected if on same host)
                      5. Select a model and start chatting
                      