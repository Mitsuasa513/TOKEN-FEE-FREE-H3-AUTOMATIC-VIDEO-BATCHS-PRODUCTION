# Required Models on ComfyUI Server

> **Note**: Exact filenames and node types vary by setup. Use config.json in the skill root to match your server. The values below are examples.

## ZIMAGE (Image Generation)

| What | Standard (bf16) | GGUF variant |
|---|---|---|
| UNET | z_image_turbo_bf16.safetensors via UNETLoader | z_image_turbo-Q8_0.gguf via UnetLoaderGGUF |
| CLIP | qwen3_4b.safetensors via CLIPLoader | Qwen3-8B-Hivemind-....gguf via CLIPLoaderGGUF |
| VAE | e.safetensors via VAELoader | same |

## MiniMax H3 (Video Generation)

| What | Standard | Custom |
|---|---|---|
| UNET | minimax_h3_fl2va_pruned_int8_convrot.safetensors | same |
| LoRA | minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors via LoraLoader | ..._int8convrot.safetensors via LoraLoaderInt8ConvRot |
| CLIP | qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors | same |
| Video VAE | minimax_h3_video_vae_fp16.safetensors | same |
| Audio VAE | minimax_h3_audio_vae_fp32.safetensors | same |

## Required Custom Nodes

| Plugin | Purpose |
|---|---|
| comfyui-minimax-h3-easy | H3 Easy loader |
| comfyui-minimax-h3-turbo | Turbo sampler |
| comfyui-minimax-h3-blockcache-T8 | Block cache T8 |
| ComfyUI-VideoHelperSuite (VHS) | Video load/save |
| ComfyUI-Manager (KJ) | SageAttention patch |
| ComfyUI-GGUF (KJ) | GGUF model loading (only if using GGUF variants) |

## VRAM Reference (8GB A2000M)

| Setting | Value |
|---|---|
| MiniMaxLowVRAMAttention.head_chunks | **5** |
| MiniMaxChunkFeedForward.chunks | 2 |
| MiniMaxChunkFeedForward.seq_threshold | 4096 |
| MiniMaxH3BlockCacheT8.residual_diff_threshold | 0.12 |
| MiniMaxH3BlockCacheT8.max_consecutive_hits | 2 |
| PathchSageAttentionKJ.sage_attention | auto |
| Sampling steps | 4 (LightX2V Turbo) or 8 (standard Turbo) |

> **Note**: head_chunks=5 is critical for 8GB VRAM. Set to 3-4 for 12GB+ cards.

## SageAttention Compatibility

| GPU | Supported? |
|---|---|
| RTX 20 series (2080, 2080 Ti, 2060) | ✅ Yes |
| RTX 30 series (3060, 3070, 3080, 3090) | ✅ Yes |
| RTX 40 series (4060, 4070, 4080, 4090) | ✅ Yes |
| RTX 50 series (5060, 5070, 5080, 5090) | ✅ Yes |
| Tesla V100 / V100SXM2 | ❌ No |
| Tesla A100 / A2000 / A6000 | ❌ No (use standard attention) |

If the GPU is 20/30/40/50 series, enable PathchSageAttentionKJ with sage_attention: auto for faster inference. Otherwise skip this node entirely.