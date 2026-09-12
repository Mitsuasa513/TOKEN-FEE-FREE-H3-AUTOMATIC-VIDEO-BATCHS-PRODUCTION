# TOKEN-FEE-FREE-H3-AUTOMATIC-VIDEO-BATCHS-PRODUCTION

Multi-segment AI video generation pipeline that runs on a ComfyUI server (remote or local). Generates a keyframe image with ZIMAGE, then produces N sequential video segments with MiniMax H3 (with last-frame chaining for story continuity), and auto-concatenates the result with ffmpeg.

## Features

- **Style-agnostic**: write any prompt (wuxia, sci-fi, documentary, daily life, etc.)
- **Flexible segment count**: 1 to N segments, each ~5 seconds
- **8GB VRAM friendly**: optimized acceleration stack (LowVRAMAttention + BlockCacheT8 + ChunkFeedForward + 4-step Turbo sampling)
- **Last-frame chaining**: each segment's tail frame becomes the next segment's first frame for seamless continuity
- **Auto ffmpeg concat**: final output is a single MP4 with audio

## Requirements

| Component | Notes |
|---|---|
| Python 3.10+ | local runtime |
| OpenCV (cv2) | last-frame extraction |
| ffmpeg | video concatenation |
| ComfyUI 0.33+ | rendering server (local or remote) |
| GPU 8GB+ VRAM | tested on RTX A2000M |

### Server-side Models

See [references/models.md](references/models.md) for the full list.

### Server-side Custom Nodes

- comfyui-minimax-h3-easy
- comfyui-minimax-h3-turbo
- comfyui-minimax-h3-blockcache-T8
- ComfyUI-VideoHelperSuite
- ComfyUI-Manager (KJ)

## Quick Start

### Install

`ash
pip install -r requirements.txt
`

### Run

`ash
python scripts/pipeline.py \
  --server http://YOUR_SERVER:8595 \
  --image-prompt "A cozy cabin in the snow at dusk" \
  --prompts "snowflakes drift past the window" "warm light glows from inside" "a figure walks toward the door" \
  --output ./output \
  --ffmpeg /path/to/ffmpeg
`

Or from Python:

`python
from scripts.pipeline import run_pipeline

run_pipeline(
    server="http://192.168.1.162:8595",
    image_prompt="A bustling night market in Shanghai",
    video_prompts=[
        "Camera pans across glowing lantern stalls",
        "Steam rises from a dumpling cart",
        "A couple laughs while sharing tanghulu",
    ],
    output_dir="./output",
)
`

## Key Parameters

| Parameter | Default | Notes |
|---|---|---|
| Image resolution | 1280x720 | ZIMAGE output |
| Video resolution | 864x480 | H3 input requirement |
| FPS | 24 | |
| Frames per segment | 125 | = 5 seconds |
| Sampling steps | 4 | LightX2V Turbo |
| head_chunks | 5 | critical for 8GB VRAM |

## Project Structure

`
TOKEN-FEE-FREE-H3-AUTOMATIC-VIDEO-BATCHS-PRODUCTION/
├── SKILL.md              # Codex skill definition (auto-loaded by agent)
├── scripts/
│   └── pipeline.py       # Main pipeline script (CLI + library)
├── references/
│   ├── models.md         # Required models & VRAM settings
│   └── workflows.md      # ComfyUI API node graphs
├── requirements.txt
└── LICENSE               # Apache 2.0
`

## How It Works

1. **Keyframe generation** — ZIMAGE produces a 1280x720 still image from your image_prompt
2. **Segment loop (xN)** — H3 generates a 5s video (864x480, 24fps) using the previous frame as irst_frame
3. **Last-frame extraction** — OpenCV grabs the tail frame of each segment locally
4. **Upload & chain** — the extracted frame is uploaded to the server as the next segment's input
5. **Concat** — ffmpeg stitches all segments into one final MP4

## License

Apache 2.0 — see [LICENSE](LICENSE)