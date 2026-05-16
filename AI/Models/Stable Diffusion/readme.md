# Stable Diffusion

## Steps (Docker Compose)
Docker Compose:
```bash
docker compose up -d
```

Browser:
```
http://localhost:7860
```

## Steps (Docker Run)
Docker Run:

```bash
docker run --gpus all -it --rm `
  -p 7860:7860 `
  -v ${PWD}\data:/data `
  -v ${PWD}\models:/models `
  -v ${PWD}\outputs:/outputs `
  ghcr.io/abdeladim-s/automatic1111:latest
```

Browser:
```
http://localhost:7860
```