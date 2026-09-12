---
name: TOKEN-FEE-FREE-H3-AUTOMATIC-VIDEO-BATCHS-PRODUCTION
description: Generate multi-segment videos via a remote ComfyUI server. Uses ZIMAGE for keyframe generation and MiniMax H3 for sequential video segments with last-frame chaining. Supports any number of segments (N x 5s). Includes auto-concatenation with ffmpeg.
metadata:
  short-description: Remote ComfyUI video pipeline (ZIMAGE + H3 multi-segment)
---

# ComfyUI Video Pipeline

Automated multi-segment video generation on a remote ComfyUI server.

## When to Use

- User asks to generate a video (or multi-part video) using a remote ComfyUI server
- User wants image-to-video with story continuity across segments
- User mentions H3, MiniMax, ZIMAGE, or the video pipeline

## Architecture

`
[Local] --HTTP--> [ComfyUI Server]
  |                   |
  |  1. Submit workflow  |  Render (ZIMAGE / H3)
  |  2. Poll history     |
  |  3. Download output  |
  |  4. Extract last frame (OpenCV)
  |  5. Upload next first frame
  |  6. Repeat N times
  |  7. ffmpeg concat
  +------------------------
`

## Required Environment

| Dependency | Purpose |
|---|---|
| Python 3.10+ | Script runtime |
| OpenCV (cv2) | Last-frame extraction |
| ffmpeg (in PATH or configured) | Video concatenation with audio |
| ComfyUI server (v0.33+) | Rendering backend |
| Models on server | See references/models.md |

## Usage

`python
from scripts.pipeline import run_pipeline

run_pipeline(
    server='http://YOUR_SERVER:8595',
    image_prompt='Your scene description for the keyframe',
    video_prompts=[
        'Segment 1 action description',
        'Segment 2 action description',
        # ... N segments, each ~5 seconds
    ],
    output_dir='./output',
)
`

Or CLI:

`ash
python scripts/pipeline.py \
  --server http://YOUR_SERVER:8595 \
  --image-prompt 'A sunlit cafe with steam rising from coffee cups' \
  --prompts 'camera slowly pans across the table' 'a hand reaches for the cup' 'morning light shifts through the window' \
  --output ./output
`

## Key Constraints (8GB VRAM)

- Image: **1280x720** (ZIMAGE)
- Video: **864x480**, 24fps, **125 frames/segment** (5s)
- H3 acceleration: MiniMaxLowVRAMAttention head_chunks=5, BlockCacheT8, ChunkFeedForward
- 4-step sampling with LightX2V Turbo LoRA
- **Interrupt between segments** to free VRAM
- **Last-frame chaining**: extract tail frame via OpenCV, upload, use as next first_frame

## Workflow Details

See references/workflows.md for the exact ComfyUI node graphs (API format).

## Troubleshooting

- **OOM**: Reduce VIDEO_LENGTH to 73 (3s) or ensure head_chunks=5
- **Shape error**: Ensure image resolution is 1280x720 (not 848x480) before feeding to H3
- **First/last frame mismatch**: Always use OpenCV extract_last_frame, NOT VHS_LoadVideo batch output
- **ffmpeg not found**: Ensure ffmpeg is in a directory the script can execute from
