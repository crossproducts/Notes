# Ollama Inference

## FastAPI Endpoints
| Method | Path| Description |
| -- | -- | -- |
| GET | /models | List locally pulled Ollama models |
| POST | /generate | Raw completion (single-turn) |
| POST | /chat | Chat completion (multi-turn format) |

## FastAPI Docs
| UI |	URL | Notes |
| -- | -- | -- |
| Swagger UI |	http://localhost:8000/docs |	Try requests directly in the browser |
| ReDoc |	http://localhost:8000/redoc |	Cleaner read-only reference |

## Suggested Ollama Models
| Lightweight | Mid-tier | Code-focused |
| :--: | :--: | :--: |
| llama3.2  | llama3.2:8b | codellama  |
| phi3  | mistral  | qwen2.5-coder |
| gemma3:1b | gemma3  |  |

## Install & Run Code
```
pip install -r requirements.txt
uvicorn main:app --reload
```

## Example Request
```
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"model": "llama3.2", "prompt": "Hello!", "stream": false}'
```