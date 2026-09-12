# Required Models on ComfyUI Server

## ZIMAGE (Image Generation)

| File | Directory |
|---|---|
| `z_image_turbo-Q8_0.gguf` | `unet/` |
| `Qwen3-8B-Hivemind-Inst-Hrtic-Ablit-Uncensored-Q4_K_M-imat.gguf` | `clip/` |
| `ae.safetensors` | `vae/` |

## MiniMax H3 (Video Generation)

| File | Directory |
|---|---|
| `minimax_h3_fl2va_pruned_int8_convrot.safetensors` | `unet/` |
| `minimax_h3_fl2v_lightx2v_turbo_4step_v0.1_comfy_int8convrot.safetensors` | `loras/` |
| `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` | `clip/` |
| `minimax_h3_video_vae_fp16.safetensors` | `vae/` |
| `minimax_h3_audio_vae_fp32.safetensors` | `vae/` |

## Required Custom Nodes

| Plugin | Purpose |
|---|---|
| `comfyui-minimax-h3-easy` | H3 Easy loader |
| `comfyui-minimax-h3-turbo` | Turbo sampler |
| `ComfyUI-MiniMaxH3-SolAttn-V100` (optional) | SolAttn acceleration |
| `comfyui-minimax-h3-blockcache-T8` | Block cache T8 |
| `ComfyUI-Manager` (KJ) | SageAttention patch |
| `ComfyUI-VideoHelperSuite` (VHS) | Video load/save |

## VRAM Reference (8GB A2000M)

| Setting | Value |
|---|---|
| `MiniMaxLowVRAMAttention.head_chunks` | **5** |
| `MiniMaxChunkFeedForward.chunks` | 2 |
| `MiniMaxChunkFeedForward.seq_threshold` | 4096 |
| `MiniMaxH3BlockCacheT8.residual_diff_threshold` | 0.12 |
| `MiniMaxH3BlockCacheT8.max_consecutive_hits` | 2 |
| `PathchSageAttentionKJ.sage_attention` | auto |
| Sampling steps | 4 (LightX2V Turbo) |

> **Note**: `head_chunks=5` is critical for 8GB VRAM. Set to 3-4 for 12GB+ cards.
