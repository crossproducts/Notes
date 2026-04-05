# Ollama

> [!NOTE]   
> **Status**: Pending
---

> Run large language models locally on your machine with a simple CLI and REST API.

## Overview

| Property | Detail |
|---|---|
| Type | Local LLM Runtime |
| Interface | CLI + REST API |
| Platforms | macOS, Linux, Windows |
| Website | https://ollama.com |
| GitHub | https://github.com/ollama/ollama |

## Installation

### macOS
```bash
brew install ollama
```

### Linux
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Windows
```
Download the installer from https://ollama.com/download
```

## CLI Commands

```bash
# Pull a model
ollama pull llama3.2

# List downloaded models
ollama list

# Remove a model
ollama rm llama3.2

# Show model info
ollama show llama3.2
```

### Running Models
```bash
# Start interactive chat
ollama run llama3.2

# Run with a prompt
ollama run llama3.2 "Explain transformers in one paragraph"

# Run in the background (starts server)
ollama serve
```

## REST API

Ollama exposes a local REST API on `http://localhost:11434`.

### Generate (single turn)
```bash
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2",
  "prompt": "Why is the sky blue?",
  "stream": false
}'
```

### Chat (multi-turn)
```bash
curl http://localhost:11434/api/chat -d '{
  "model": "llama3.2",
  "messages": [
    {
      "role": "user",
      "content": "What is RAG?"
    }
  ],
  "stream": false
}'
```

### List Models
```bash
curl http://localhost:11434/api/tags
```

## Python Integration

### Using the `ollama` Package
```python
import ollama

# Simple generation
response = ollama.generate(model='llama3.2', prompt='Hello!')
print(response['response'])

# Chat
response = ollama.chat(model='llama3.2', messages=[
{ 'role': 'user', 'content': 'What is machine learning?' }
])
print(response['message']['content'])
```

### Using OpenAI-Compatible Endpoint
```python
from openai import OpenAI

client = OpenAI(
base_url='http://localhost:11434/v1',
api_key='ollama',  # required but unused
)

response = client.chat.completions.create(
model='llama3.2',
messages=[{'role': 'user', 'content': 'Hello!'}]
)
print(response.choices[0].message.content)
```

### Using with LangChain
```python
from langchain_ollama import OllamaLLM

llm = OllamaLLM(model='llama3.2')
result = llm.invoke('Tell me a joke')
print(result)
```

## Popular Models

| Model | Size | Use Case |
|---|---|---|
| llama3.2 | 3B / 1B | General chat, fast inference |
| llama3.1 | 8B / 70B | General purpose, strong reasoning |
| mistral | 7B | Instruction following, coding |
| codellama | 7B / 13B | Code generation and explanation |
| phi3 | 3.8B / 14B | Microsoft small model, efficient |
| gemma2 | 2B / 9B / 27B | Google model, multilingual |
| qwen2.5 | 0.5B–72B | Alibaba model, coding & math |
| nomic-embed-text | 137M | Text embeddings |
| mxbai-embed-large | 335M | High quality embeddings |

## Modelfile (Custom Models)

Create a `Modelfile` to customise a model's behaviour:

```dockerfile
FROM llama3.2

# Set system prompt
SYSTEM """
You are a helpful assistant that answers concisely.
"""

# Set parameters
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER num_ctx 4096
```

```bash
# Build and run custom model
ollama create my-assistant -f Modelfile
ollama run my-assistant
```

## Key Parameters

| Parameter | Description | Default |
|---|---|---|
| `temperature` | Randomness of output (0=deterministic, 1=creative) | 0.8 |
| `top_p` | Nucleus sampling probability | 0.9 |
| `top_k` | Top-k tokens to sample from | 40 |
| `num_ctx` | Context window size (tokens) | 2048 |
| `num_predict` | Max tokens to generate (-1 = unlimited) | 128 |
| `repeat_penalty` | Penalty for repeated tokens | 1.271 |

## GPU Acceleration

Ollama automatically uses GPU if available.

```bash
# Check GPU usage
ollama ps

# Force CPU only
OLLAMA_NO_GPU=1 ollama serve
```

### Supported Backends
- **NVIDIA** – CUDA (Linux & Windows)
- **AMD** – ROCm (Linux)
- **Apple Silicon** – Metal (macOS)

## Environment Variables

| Variable | Description |
|---|---|
| `OLLAMA_HOST` | Bind address (default: `127.0.0.1:11434`) |
| `OLLAMA_MODELS` | Custom models directory |
| `OLLAMA_NUM_PARALLEL` | Parallel request limit |
| `OLLAMA_MAX_LOADED_MODELS` | Max models kept in memory |
| `OLLAMA_KEEP_ALIVE` | How long to keep model in memory (e.g. `5m`) |

## References

- [Ollama Docs](https://github.com/ollama/ollama/blob/main/docs/README.md)
- [Ollama Model Library](https://ollama.com/library)
- [Ollama REST API Docs](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [Ollama Python SDK](https://github.com/ollama/ollama-python)
- [Youtube: Ollama in 100 Seconds – Fireship](https://www.youtube.com/watch?v=90ozfdsQOKo)