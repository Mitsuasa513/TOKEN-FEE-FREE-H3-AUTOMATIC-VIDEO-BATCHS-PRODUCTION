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

## First-Time Setup Check

Before running the pipeline, verify ALL of the following in one pass:

1. **Python 3.10+** — python --version
2. **OpenCV** — python -c "import cv2; print(cv2.__version__)" (if missing: pip install opencv-python)
3. **ffmpeg** — where ffmpeg (Windows) or which ffmpeg (Linux/Mac). If not found, STOP and ask user to install it. Do NOT guess paths.
4. **ComfyUI server reachable** — curl -s http://SERVER:PORT/system_stats should return JSON. If it fails, STOP and ask user for the correct address.
5. **GPU VRAM >= 8GB** — check via 
vidia-smi or ComfyUI system_stats.
6. **h3-prompt-writing skill installed** — verify the h3-prompt-writing skill exists (check ~/.agents/skills/h3-prompt-writing/SKILL.md or ~/.codex/skills/h3-prompt-writing/SKILL.md). All video segment prompts MUST be formatted through this skill before submission to H3. If missing, ask the user to install it: https://github.com/Mitsuasa513/h3-prompt-writing

If any check fails, tell the user what's missing and how to fix it. Do not proceed.

## Prompt Formatting (REQUIRED)

Before submitting any video segment prompt to the H3 workflow, you MUST run it through the h3-prompt-writing skill to produce the correct integrated_multimodal_description + overall_soundscape + 
on_diegetic_music structure. Plain freeform text will not produce quality results.

Workflow:
1. Write the raw narrative intent for each segment (e.g. "camera pans left, the warrior draws his sword")
2. Invoke the h3-prompt-writing skill to reformat into H3-compatible structured prompt
3. Use the formatted output as the prompt field in the MiniMaxH3ImageToVideo node

This applies to ALL segments (1 through N). The ZIMAGE keyframe prompt does NOT need this formatting.

## Server Address (IMPORTANT)

**Do NOT assume a default server address.** On first use, ask the user:

> "Is your ComfyUI running locally (e.g. http://127.0.0.1:8595) or on a remote machine? If remote, please provide the IP and port."

Use the user's answer as the --server argument for all subsequent calls in the session.

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
