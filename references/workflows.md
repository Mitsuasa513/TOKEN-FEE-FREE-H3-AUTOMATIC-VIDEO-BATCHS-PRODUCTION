# ComfyUI API Workflow Formats

## ZIMAGE Image Generation

```json
{
  "1": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
  "2": {"class_type": "UnetLoaderGGUF", "inputs": {"unet_name": "z_image_turbo-Q8_0.gguf"}},
  "3": {"class_type": "CLIPLoaderGGUF", "inputs": {"clip_name": "Qwen3-8B-....gguf", "type": "stable_diffusion"}},
  "4": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["3",0], "text": "YOUR PROMPT"}},
  "5": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["3",0], "text": "negative prompt"}},
  "6": {"class_type": "ModelSamplingAuraFlow", "inputs": {"model": ["2",0], "shift": 3.0}},
  "7": {"class_type": "EmptySD3LatentImage", "inputs": {"width": 1280, "height": 720, "batch_size": 1}},
  "8": {"class_type": "KSampler", "inputs": {"model": ["6",0], "seed": 42, "steps": 9, "cfg": 1, "sampler_name": "res_multistep", "scheduler": "simple", "positive": ["4",0], "negative": ["5",0], "latent_image": ["7",0], "denoise": 1}},
  "9": {"class_type": "VAEDecode", "inputs": {"samples": ["8",0], "vae": ["1",0]}},
  "10": {"class_type": "SaveImage", "inputs": {"images": ["9",0], "filename_prefix": "output"}}
}
```

## MiniMax H3 Video Generation (with acceleration)

Node chain:
```
UNETLoader -> PathchSageAttentionKJ -> ModelPatchTorchSettings -> LoraLoaderInt8ConvRot
  -> MiniMaxChunkFeedForward -> MiniMaxLowVRAMAttention -> MiniMaxH3BlockCacheT8
    -> BasicGuider / BasicScheduler (both take model from BlockCacheT8)
```

Key parameters:
- `MiniMaxH3ImageToVideo`: width=864, height=480, length=125, first_frame=IMAGE
- `MiniMaxLowVRAMAttention`: head_chunks=5
- `MiniMaxH3BlockCacheT8`: residual_diff_threshold=0.12, max_consecutive_hits=2, cache_device=cpu, metric_stride=8
- `BasicScheduler`: scheduler=simple, steps=4, denoise=1.0
- `KSamplerSelect`: sampler_name=res_multistep
- `CreateVideo`: fps=24, bit_depth=8
