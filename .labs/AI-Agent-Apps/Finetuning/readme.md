# Fine Tuning

## Fine-Tuning Tech Stack
| Tool | Specialty | 
| -- | -- |
| **AWS Bedrock** | AWS Managed Fine-Tuning Foundational Models |
| **TorchTune** | Rapid scaling and efficient experimentation for large language model fine-tuning |
| **SFTTrainer** | Simplifies supervised fine-tuning across multiple transformer models |
| **Unsloth** | Optimized for fine-tuning on limited hardware with reduced memory and compute requirements |
| **Axolotl** | Flexible configuration for fine-tuning workflows with minimal setup overhead |
| **DeepSpeed + FSDP** | Distributed Training at scale |


## Fine-Tuning Techniques
| Technique | Type | Description |
| -- | -- | -- |
| **Full Fine-Tuning** | Training | Updates all model weights — highest quality, requires many GPUs |
| **SFT** (Supervised Fine-Tuning) | Training | Train on labeled input/output pairs — most common starting point |
| **LoRA** (Low-Rank Adaptation) | Parameter | Freezes base weights, trains small adapter matrices (~1% of params) |
| **QLoRA** (Quantized LoRA) | Memory | Compresses base model to 4-bit, trains LoRA adapters in full precision |
| **RLHF** (Reinforcement Learning from Human Feedback) | Alignment | Uses human preference data + reward model to align outputs |
| **DPO** (Direct Preference Optimization) | Alignment | Simpler RLHF alternative — trains directly on preference pairs, no reward model needed |
| **PPO** (Proximal Policy Optimization) | Alignment | Reinforcement learning optimizer used inside RLHF pipelines |


## Tool × Technique Compatibility
| Tool | Full FT | SFT | LoRA | QLoRA | DPO | RLHF/PPO |
| -- | -- | -- | -- | -- | -- | -- |
| **Unsloth** | - | yes | yes | yes | yes | - |
| **Axolotl** | yes | yes | yes | yes | yes | limited |
| **TRL (SFTTrainer)** | yes | yes | yes | yes | yes | yes |
| **TorchTune** | yes | yes | yes | - | yes | - |
| **LLaMA-Factory** | yes | yes | yes | yes | yes | yes |
| **OpenAI API** | - | yes | - | - | - | - |
| **Vertex AI / Bedrock** | - | yes | - | - | - | limited |
| **DeepSpeed + FSDP** | yes | yes | yes | yes | yes | yes |


## Fine Tuning Guides
- [DataCamp: Fine Tuning with llama 3](https://app.datacamp.com/learn/courses/fine-tuning-with-llama-3)
- [Youtube: Tech With Tim - Fine-Tune a LLM and Use It With Ollama](https://www.youtube.com/watch?v=pTaSDVz0gok)
- [Youtube: NeuralNine - Fine-Tuning Local LLMs with Unsloth & Ollama](https://www.youtube.com/watch?v=W_xh6qNSfAQ)
- [Youtube: Warp - Fine-Tune a LLM and Use It With Ollama](https://www.youtube.com/watch?v=pxhkDaKzBaY)
- [Youtube: Fine-tune your own LLM in 13 minutes](https://www.youtube.com/watch?v=g80Q1sVtikE)
- [Youtube: Fine-Tune A Large Language Model](https://www.youtube.com/watch?v=pddeyCqevnw)
- [DataCamp: Fine Tuning with llama 4](https://www.datacamp.com/tutorial/fine-tuning-llama-4)
- [DataCamp: Fine-Tuning DeepSeek R1](https://www.datacamp.com/tutorial/fine-tuning-deepseek-r1-reasoning-model)
    - [Youtube: Fine-Tuning DeepSeek R1](https://www.youtube.com/watch?v=qcNmOItRw4U)
- [DataCamp: Optimize LLMs with Llama Fine-tuning](https://app.datacamp.com/learn/projects/2827)
- [Youtube: Fine-tuning Open Source LLMs with Mistral](https://www.youtube.com/watch?v=SnGXzb0adLQ)
