# Unsloth Fine-Tuning — Lab 1

Supervised Fine-Tuning (SFT) of LLaMA 3.1 8B using LoRA adapters, optimized for Google Colab free tier.

## What This Lab Covers

- Loading a 4-bit quantized LLM with Unsloth
- Attaching LoRA adapters (train ~1% of params)
- Formatting an instruction dataset (Alpaca-style)
- Training with SFTTrainer
- Running inference on the fine-tuned model
- Saving in multiple formats (LoRA adapter, merged 16-bit, GGUF for Ollama)

---

## Why Unsloth

| Feature | Benefit |
|---------|---------|
| 2x faster training | Triton-optimized CUDA kernels |
| 70% less VRAM | Fits LLaMA 3.1 8B on free T4 (15GB) |
| 4-bit quantization | QLoRA support out of the box |
| Drop-in HuggingFace | Uses standard `SFTTrainer` / `transformers` API |
| GGUF export | Direct export for Ollama / llama.cpp |

---

## Hardware Requirements

| GPU | Model Size | Notes |
|-----|-----------|-------|
| T4 15GB (Colab Free) | 7B–8B (4-bit) | Works with `LOAD_IN_4BIT=True` |
| A100 40GB (Colab Pro) | 13B–70B (4-bit) | Use `bfloat16` |
| RTX 3090/4090 (local) | 7B–13B (4-bit) | Same code, no changes needed |

---

## Colab Setup

1. Open a new Colab notebook
2. Set runtime: **Runtime > Change runtime type > T4 GPU**
3. Run the install cell first:
```python
!pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
!pip install --no-deps trl peft accelerate bitsandbytes
```
4. Upload `finetune.ipynb` and run cells top to bottom

---

## Key Concepts

### LoRA (Low-Rank Adaptation)
Instead of updating all model weights, LoRA injects small trainable matrices into attention layers. This reduces trainable parameters from ~8B down to ~20M, making fine-tuning feasible on consumer hardware.

```
Full fine-tuning:  8,000,000,000 params updated
LoRA fine-tuning:     20,000,000 params updated  (~0.25%)
```

### QLoRA
Combines 4-bit quantization (NF4) with LoRA. The base model is frozen and compressed; only the LoRA adapters are trained in full precision. This is what `LOAD_IN_4BIT=True` enables.

### Alpaca Prompt Format
```
### Instruction:
<task description>

### Input:
<optional context>

### Response:
<expected output>
```
Any instruction-following dataset can be formatted this way. The `format_prompts` function handles this mapping.

---

## Tuning Parameters

| Parameter | Default | Notes |
|-----------|---------|-------|
| `r` | 16 | LoRA rank — higher = more capacity, more VRAM |
| `lora_alpha` | 16 | Usually set equal to `r` |
| `max_steps` | 60 | Increase to `500+` or use `num_train_epochs=1` |
| `learning_rate` | 2e-4 | Standard for LoRA; lower for larger datasets |
| `per_device_train_batch_size` | 2 | Increase if VRAM allows |
| `gradient_accumulation_steps` | 4 | Effective batch = batch_size × accum_steps |

---

## Dataset Options

Swap `yahma/alpaca-cleaned` with any HuggingFace dataset or your own data:

```python
# Custom JSONL dataset
dataset = load_dataset("json", data_files="my_data.jsonl", split="train")

# HuggingFace dataset
dataset = load_dataset("teknium/OpenHermes-2.5", split="train")

# Custom format — just map to {"instruction", "input", "output"} fields
```

### Minimum Dataset Size
- **Quick test**: 100–500 examples
- **Noticeable behavior change**: 1,000–5,000 examples
- **Strong domain adaptation**: 10,000+ examples

---

## Output Formats

| Format | Use Case | Size |
|--------|----------|------|
| LoRA adapter only | Continue training, merge later | ~100MB |
| Merged 16-bit | vLLM, HuggingFace inference | ~16GB |
| GGUF q4_k_m | Ollama, llama.cpp, local use | ~4.5GB |
| Push to Hub | Share on HuggingFace | varies |

---

## Using the Fine-Tuned Model with Ollama

After exporting as GGUF:

```bash
# 1. Create a Modelfile
echo 'FROM ./model_gguf/unsloth.Q4_K_M.gguf' > Modelfile

# 2. Create the Ollama model
ollama create my-finetuned-model -f Modelfile

# 3. Run it
ollama run my-finetuned-model
```

---

## Common Errors

| Error | Fix |
|-------|-----|
| `CUDA out of memory` | Lower `r`, reduce batch size, enable `packing=True` |
| `RuntimeError: slow_conv2d_cpu` | Ensure you're on GPU runtime in Colab |
| `Module not found: unsloth` | Re-run the install cell |
| Repetitive/incoherent output | Missing `EOS_TOKEN` at end of training examples |

---

## Next Steps

- **Lab 2**: Fine-tune on a custom domain dataset (e.g., medical, legal, code)
- **Lab 3**: RLHF with reward modeling using TRL's `PPOTrainer`
- **Lab 4**: Export and serve with vLLM for production throughput
