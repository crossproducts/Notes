# Computer Vision

> Reference for CV tasks, architectures, datasets, and metrics.
> See [ai-ml-dl-readme.md](ai-ml-dl-readme.md) for CNN/ViT architectures and [ai-llm-readme.md](ai-llm-readme.md) for multimodal LLMs.
> See [!HuggingFace](../!HuggingFace/) for pre-trained vision models.

## CV Task Taxonomy

```
Image Input
    │
    ├── Image Classification        → "Is this a cat or dog?"
    │
    ├── Object Detection            → "Where are all the cars? Draw bounding boxes."
    │   ├── One-stage: YOLO, SSD, RetinaNet
    │   └── Two-stage: Faster R-CNN, Mask R-CNN
    │
    ├── Semantic Segmentation       → Label every pixel with a class
    │   └── FCN, DeepLab, SegFormer
    │
    ├── Instance Segmentation       → Separate mask per object instance
    │   └── Mask R-CNN, YOLO-Seg
    │
    ├── Panoptic Segmentation       → Semantic + Instance combined
    │
    ├── Keypoint / Pose Estimation  → Human skeleton, facial landmarks
    │   └── OpenPose, MediaPipe, ViTPose
    │
    ├── Depth Estimation            → Predict per-pixel depth
    │
    ├── Image Generation
    │   ├── GANs                    → StyleGAN, BigGAN
    │   ├── Diffusion Models        → Stable Diffusion, DALL-E 3, Midjourney
    │   └── VAEs                    → Variational Autoencoders
    │
    ├── Image-Text
    │   ├── Image Captioning        → BLIP-2, LLaVA
    │   ├── Visual QA (VQA)        → Answer questions about images
    │   └── CLIP                    → Zero-shot image-text matching
    │
    └── Video Understanding
        ├── Action Recognition      → "Person is running"
        ├── Video Segmentation
        └── Optical Flow
```

## Key Architectures

| Architecture | Year | Notes |
|---|---|---|
| AlexNet | 2012 | First deep CNN to win ImageNet |
| VGG-16/19 | 2014 | Very deep, simple 3×3 convolutions |
| ResNet | 2015 | Residual connections — enabled very deep networks |
| EfficientNet | 2019 | NAS-optimised, excellent accuracy/compute tradeoff |
| Vision Transformer (ViT) | 2020 | Patches as tokens, pure Transformer |
| Swin Transformer | 2021 | Hierarchical ViT with shifted windows |
| DINOv2 | 2023 | Self-supervised ViT, strong features |
| YOLO (v8/v9/v11) | 2023+ | Real-time object detection |
| Faster R-CNN | 2015 | Region proposal network + classifier |
| Mask R-CNN | 2017 | Faster R-CNN + segmentation mask |
| SAM (Segment Anything) | 2023 | Foundation model for segmentation (Meta) |
| CLIP | 2021 | Contrastive image-text pre-training (OpenAI) |
| Stable Diffusion | 2022 | Latent diffusion model for image generation |

## Evaluation Metrics

| Task | Metric | Description |
|---|---|---|
| Classification | Top-1 / Top-5 Accuracy | % correct (best guess / in top 5) |
| Classification | Precision, Recall, F1 | Per-class and macro/micro |
| Object Detection | mAP (mean Average Precision) | Average AP across IoU thresholds and classes |
| Object Detection | IoU (Intersection over Union) | Overlap of predicted vs ground truth box |
| Segmentation | mIoU (mean IoU) | Average IoU across all classes |
| Segmentation | Dice Coefficient | 2×(A∩B)/(A+B) — similar to F1 |
| Image Generation | FID (Fréchet Inception Distance) | Distance between real/generated feature distributions |
| Image Generation | IS (Inception Score) | Quality + diversity of generated images |
| Image Generation | LPIPS | Learned perceptual similarity |
| Depth Estimation | AbsRel, RMSE | Absolute relative error, root mean squared |

## Data Augmentation

| Technique | Description |
|---|---|
| Random crop + flip | Spatial invariance |
| Color jitter | Brightness, contrast, saturation, hue |
| Rotation / shear | Geometric variation |
| CutOut / Random Erasing | Occlude regions, improve robustness |
| MixUp | Blend two images + interpolate labels |
| CutMix | Paste patch from one image into another |
| AutoAugment / RandAugment | Learned augmentation policies |
| Mosaic (YOLO) | Combine 4 images into one |

## Key Datasets

| Dataset | Task | Size | Notes |
|---|---|---|---|
| ImageNet | Classification | 1.2M images, 1000 classes | Standard benchmark |
| COCO | Detection, segmentation | 330K images, 80 classes | Standard detection benchmark |
| Open Images | Detection, segmentation | 9M images | Large-scale |
| PASCAL VOC | Detection | 20 classes | Classic benchmark |
| CelebA | Face attributes | 200K faces | Face detection / generation |
| ADE20K | Semantic segmentation | 20K images, 150 classes | Dense labels |
| Cityscapes | Autonomous driving seg. | 5K images, 19 classes | Urban scenes |

## Transfer Learning for Vision

```
Pre-trained backbone (ImageNet)
    │
    ├── Feature extraction: freeze backbone, train new head
    │     → Fast, works with small data (~100s of images)
    │
    └── Fine-tuning: unfreeze some or all layers
          → Better performance with more data (~1000s of images)

Common backbones: ResNet, EfficientNet, ViT, Swin, DINOv2
```

## References

- [ai-ml-dl-readme.md](ai-ml-dl-readme.md) — CNN / ViT architectures
- [ai-llm-readme.md](ai-llm-readme.md) — Multimodal LLMs (GPT-4o, Gemini)
- [!HuggingFace](../!HuggingFace/) — Pre-trained vision models
- [Papers With Code — Computer Vision](https://paperswithcode.com/area/computer-vision)
- [Ultralytics YOLO Documentation](https://docs.ultralytics.com/)
- [torchvision Documentation](https://pytorch.org/vision/stable/index.html)
