# TOKEN-FEE-FREE-H3-AUTOMATIC-VIDEO-BATCHS-PRODUCTION / 省TOKEN钱！本地导演指挥自动视频生产流水线

Multi-segment AI video generation pipeline that runs on a ComfyUI server (remote or local). Generates a keyframe image with ZIMAGE(CAN BE FOUND IN COMFYUI TEMPLATE), then produces N sequential video segments with MiniMax H3 (with last-frame chaining for story continuity), and auto-concatenates the result with ffmpeg.  
🦉Currently directed by Qwen3 27B, with plans to test smaller models in the future.

基于 ComfyUI 服务器（本地或远程）的多段式 AI 视频生成流水线。先用 ZIMAGE 工作流（你可以在COMFYUI模板找到）生成关键帧图像，再通过 MiniMax H3 依次生成 N 段连续视频（采用"尾帧衔接"保证剧情连贯），最后用 ffmpeg 自动拼接成完整视频。  
🦉目前由Qwen3.8 27b担任导演，后续还将测试更小的模型尝试。

## Features / 特点

- **Style-agnostic**: write any prompt (wuxia, sci-fi, documentary, daily life, etc.)
- **Flexible segment count**: 1 to N segments, each ~5 seconds due to performance downgrade cased by accumulating contextures, it is recommended to use /compress or start a new thread, or use hermes(recommend)
- **8GB VRAM friendly**: V100 optimized acceleration stack also for 20 30 40 50 Series card(LowVRAMAttention + BlockCacheT8 + ChunkFeedForward + 4-step Turbo sampling)
- **Last-frame chaining**: each segment's tail frame becomes the next segment's first frame for seamless continuity
- **Auto ffmpeg concat**: final output is a single MP4 with audio

- **风格无关**：支持任意风格的提示词（武侠、科幻、纪录片、日常生活等）
- **段数灵活**：可生成 1 到 N 段，每段约 5 秒，出于上下文考虑建议长时间运行开个新的线程或者压缩上下文，或者使用hermes
- **8GB 显存友好**：V100专用工作流优化的加速方案也可以给20 30 40 50显卡使用（LowVRAMAttention + BlockCacheT8 + ChunkFeedForward + 4 步 Turbo 采样）
- **尾帧衔接**：每段的最后一帧自动作为下一段的首帧，实现无缝连贯
- **ffmpeg 自动拼接**：最终输出为带音频的单个 MP4 文件

## Requirements / 环境需求

| Component | Notes |
|---|---|
| Python 3.10+ | local runtime |
| OpenCV (cv2) | last-frame extraction |
| ffmpeg | video concatenation |
| ComfyUI 0.33+ | rendering server (local or remote) |
| VIDEO PRODUCER: RTX-A2000M-8GB+32G（SAME AS RTX 3050） RAM+Comfyui 0.33| OK, Test Passed |
| DIRECTOR: V100-32G-SXM2+96G RAM+Codex+Qwen3.8 27B  | OK, Test Passed |

| 组件            | 说明                          |
| ------------- | --------------------------- |
| Python 3.10+  | 本地运行环境                     |
| OpenCV (cv2)  | 用于提取尾帧                    |
| ffmpeg        | 视频拼接                      |
| ComfyUI 0.33+ | 渲染服务器（本地或远程）              |
| GPU 8GB+ 显存  | 已在 RTX A2000M（同3050） 上测试通过         |
| V100-32G SXM2  | 导演：Qwen3.8 27B+Codex 测试通过     |

TEST PROMPT(VERY EASY AND THE MODEL WITH THIS SKILL WILL AUTOMATICLLY SET UP SCRIPTS): A 30-second wuxia martial arts short film. The scene features a deadly assassin, a skilled female swordsman, and intense close combat.
测试提示词(很简单，剩下的模型自己会写脚本导演): 我要一段30秒的武侠片，包括刺客、女侠和打斗画面。
| Sample 1  (FROM 0:15 OF VIDEO) | Sample 2  (FROM 0:25 OF VIDEO) |
|:--------:|:--------:|
| ![wuxia-clip](SAMPLE_IMAGES/wuxia-clip.gif) | ![wuxia-clip3](SAMPLE_IMAGES/wuxia-clip3.gif) |


### SPECIAL RECOMMENDED Prerequisites / 特别推荐先安装的前置
- Install the official **MiniMax H3 Prompt Writing** skill first: (https://github.com/MiniMax-AI/MiniMax-H3/tree/main/skills/h3-prompt-writing)
  This project depends on its prompt structure for H3 model input. This skill will helps write prompt better.
- 安装官方的H3 prompt writing skill,会极大提升模型写提示词时的智商.链接在上面↑
### STRONGLY RECOMMEND USE WITH ComfyUI-MiniMax-H3-V100-Workflow
- Tested by Author, get single-pic workflows from (https://github.com/Mitsuasa513/ComfyUI-MiniMax-H3-V100-Workflow/tree/main) or this repository\workflows\
- 强强联手就是好，使用单图参考工作流，使用链接和说明书点上面，工作流本仓库也提供了↑

### Server-side Models

See [references/models.md](references/models.md) for the full list. almost same as _ComfyUI-MiniMax-H3-V100-Workflow_ 可以从H3官方下载模型和作者那里下载加速，然后加载_ComfyUI-MiniMax-H3-V100-Workflow_工作流即可。

### Server-side Custom Nodes
ALREADY INCLUDED IN THE _ComfyUI-MiniMax-H3-V100-Workflow_ 🐱
- comfyui-minimax-h3-easy
- comfyui-minimax-h3-turbo
- comfyui-minimax-h3-blockcache-T8
- ComfyUI-VideoHelperSuite
- ComfyUI-Manager (KJ)
这些加速节点已经在 _ComfyUI-MiniMax-H3-V100-Workflow_ 项目中了，直接加载工作流即可。🐱

## Quick Start / 快速开始

### Install / 安装

pip install -r requirements.txt

OR SEND THIS REPOSITORY(COPY LINK) TO YOUR AGENT AND IT WILL INSTALL AUTOMATICALLY🐙.（RECOMMENDED）
复制链接，告诉你的Agent我要装这个skill即可🐙。（推荐）


### How to Run？ / 怎么运行？

JUST TELL YOUR AGENT THE PROMPT AND EXPAND YOUR IMAGINATION:)
告诉Agent你想生成什么就好，发挥想象力：）

## Key Parameters / 主要参数

| Parameter | Default | Notes |
|---|---|---|
| Image resolution | 1280x720 | ZIMAGE output |
| Video resolution | 864x480 | H3 input requirement |
| FPS | 24 | |
| Frames per segment | 125 | = 5 seconds |
| Sampling steps | 4 | LightX2V Turbo |
| head_chunks | 5 | critical for 8GB VRAM |

| 参数             | 默认值    | 说明                        |
| -------------- | ------ | ------------------------- |
| 图像分辨率          | 1280x720 | ZIMAGE 输出                |
| 视频分辨率          | 864x480  | H3 输入要求                  |
| 帧率 (FPS)       | 24     |                           |
| 每段帧数           | 125    | = 5 秒                     |
| 采样步数           | 4      | LightX2V Turbo            |
| head\_chunks   | 5      | 8GB 显存下的关键参数            |


## Project Structure / 文件结构

- SKILL.md — Codex skill definition (auto-loaded by agent)
- scripts/pipeline.py — Main pipeline script (CLI + library)
- references/models.md — Required models & VRAM settings
- references/workflows.md — ComfyUI API node graphs
- requirements.txt — Python dependencies
- LICENSE — Apache 2.0
- SAMPLE_IMAGES/ — Demo clips

## How It Works / 工作流程

1. **Keyframe generation** — ZIMAGE produces a 1280x720 still image from your image_prompt
2. **Segment loop (xN)** — H3 generates a 5s video (864x480, 24fps) using the previous frame as irst_frame
3. **Last-frame extraction** — OpenCV grabs the tail frame of each segment locally
4. **Upload & chain** — the extracted frame is uploaded to the server as the next segment's input
5. **Concat** — ffmpeg stitches all segments into one final MP4  
  
一、关键帧生成：ZIMAGE 根据 `image_prompt` 生成 1280x720 的静态图像  
二、分段渲染：H3 以上一帧作为 `first_frame`，生成 5 秒视频（864x480, 24fps），根据用户需要生成视频  
三、尾帧提取：OpenCV 在本地提取每段的最后一帧  
四、上传视频：将提取的尾帧上传到服务器，作为下一段的输入  
五、合并优化：将所有片段拼接为一个完整的 MP4  

## License / 许可证信息

Apache 2.0 — see [LICENSE](LICENSE)
