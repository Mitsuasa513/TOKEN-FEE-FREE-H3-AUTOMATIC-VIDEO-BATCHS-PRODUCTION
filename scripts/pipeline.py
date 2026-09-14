#!/usr/bin/env python3
"""
ComfyUI Multi-Segment Video Pipeline
Generates a keyframe image (ZIMAGE) + N video segments (MiniMax H3) with last-frame chaining.
"""
import json
import time
import urllib.request
import urllib.error
import os
import sys
import subprocess
import uuid
import argparse

DEFAULT_SERVER = "http://192.168.1.162:8595"
IMAGE_SIZE = (1280, 720)
VIDEO_WIDTH = 864
VIDEO_HEIGHT = 480
VIDEO_LENGTH = 125
FPS = 24
NEGATIVE_PROMPT = "low quality, blurry, cartoon, anime, ugly, deformed, watermark, text, logo, extra limbs, bad anatomy"


def submit_workflow(server, workflow):
    payload = json.dumps({"prompt": workflow}).encode("utf-8")
    req = urllib.request.Request(
        server + "/prompt", data=payload,
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        return json.loads(resp.read()).get("prompt_id")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise Exception("Submit failed: HTTP %d\n%s" % (e.code, body[:2000]))


def wait_for_completion(server, prompt_id, timeout=1200):
    elapsed = 0
    while elapsed < timeout:
        try:
            raw = urllib.request.urlopen(server + "/history/" + prompt_id, timeout=5).read().decode()
            d = json.loads(raw) if raw.strip() else {}
            entry = list(d.values())[0] if d else {}
            status = entry.get("status", {}).get("status_str", "unknown")
            if status == "success":
                files = []
                for o in entry.get("outputs", {}).values():
                    for v in o.values():
                        if isinstance(v, list):
                            for f in v:
                                if isinstance(f, dict) and "filename" in f:
                                    files.append(f)
                return files
            elif status == "error":
                for m in entry.get("status", {}).get("messages", []):
                    if isinstance(m, list) and m and m[0] == "execution_error":
                        raise Exception("Render error: " + json.dumps(m[1], ensure_ascii=False)[:800])
        except Exception as e:
            if "Render error" in str(e):
                raise
        sys.stdout.write("  Rendering... %.0fs\r" % elapsed)
        sys.stdout.flush()
        time.sleep(15)
        elapsed += 15
    raise Exception("Timeout after %ds" % timeout)


def download_file(server, filename, subfolder, local_path):
    url = "%s/view?filename=%s&type=output&subfolder=%s&timestamp=0" % (server, filename, subfolder)
    urllib.request.urlretrieve(url, local_path)


def upload_file(server, local_path, remote_name=None):
    if remote_name is None:
        remote_name = os.path.basename(local_path)
    boundary = "----FormBoundary" + uuid.uuid4().hex
    with open(local_path, "rb") as f:
        data = f.read()
    ext = os.path.splitext(remote_name)[1].lower()
    mime = "image/png" if ext in (".png", ".jpg", ".jpeg") else "video/mp4"
    body = b""
    body += ("--" + boundary + "\r\n").encode()
    body += ('Content-Disposition: form-data; name="image"; filename="%s"\r\n' % remote_name).encode()
    body += ("Content-Type: %s\r\n\r\n" % mime).encode()
    body += data + b"\r\n"
    body += ("--" + boundary + "\r\n").encode()
    body += b'Content-Disposition: form-data; name="overwrite"\r\n\r\ntrue\r\n'
    body += ("--" + boundary + "--\r\n").encode()
    req = urllib.request.Request(
        server + "/upload/image", data=body,
        headers={"Content-Type": "multipart/form-data; boundary=" + boundary},
        method="POST")
    return json.loads(urllib.request.urlopen(req, timeout=30).read())


def interrupt(server):
    urllib.request.urlopen(
        urllib.request.Request(server + "/interrupt", method="POST", data=b""),
        timeout=5)


def extract_last_frame(video_path, output_png):
    import cv2
    cap = cv2.VideoCapture(video_path)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.set(cv2.CAP_PROP_POS_FRAMES, total - 1)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        cap = cv2.VideoCapture(video_path)
        frames = []
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(frame)
        cap.release()
        if not frames:
            raise Exception("Cannot read video: %s" % video_path)
        frame = frames[-1]
    cv2.imwrite(output_png, frame)
    return output_png


def build_zimage_workflow(image_prompt, width=IMAGE_SIZE[0], height=IMAGE_SIZE[1]):
    return {
        "1": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
        "2": {"class_type": "UnetLoaderGGUF", "inputs": {"unet_name": "z_image_turbo-Q8_0.gguf"}},
        "3": {"class_type": "CLIPLoaderGGUF", "inputs": {"clip_name": "Qwen3-8B-Hivemind-Inst-Hrtic-Ablit-Uncensored-Q4_K_M-imat.gguf", "type": "stable_diffusion"}},
        "4": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["3", 0], "text": image_prompt}},
        "5": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["3", 0], "text": NEGATIVE_PROMPT}},
        "6": {"class_type": "ModelSamplingAuraFlow", "inputs": {"model": ["2", 0], "shift": 3.0}},
        "7": {"class_type": "EmptySD3LatentImage", "inputs": {"width": width, "height": height, "batch_size": 1}},
        "8": {"class_type": "KSampler", "inputs": {"model": ["6", 0], "seed": 42, "steps": 9, "cfg": 1, "sampler_name": "res_multistep", "scheduler": "simple", "positive": ["4", 0], "negative": ["5", 0], "latent_image": ["7", 0], "denoise": 1}},
        "9": {"class_type": "VAEDecode", "inputs": {"samples": ["8", 0], "vae": ["1", 0]}},
        "10": {"class_type": "SaveImage", "inputs": {"images": ["9", 0], "filename_prefix": "pipeline-image"}},
    }


def build_h3_workflow(first_frame_ref, prompt, seed_offset=0, width=VIDEO_WIDTH, height=VIDEO_HEIGHT, length=VIDEO_LENGTH):
    return {
        "1": {"class_type": "VAELoader", "inputs": {"vae_name": "minimax_h3_video_vae_fp16.safetensors"}},
        "2": {"class_type": "VAELoader", "inputs": {"vae_name": "minimax_h3_audio_vae_fp32.safetensors"}},
        "3": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors", "type": "minimax", "device": "default"}},
        "5": {"class_type": "UNETLoader", "inputs": {"unet_name": "minimax_h3_fl2va_pruned_int8_convrot.safetensors", "weight_dtype": "default"}},
        "6": {"class_type": "PathchSageAttentionKJ", "inputs": {"model": ["5", 0], "sage_attention": "auto", "allow_compile": False}},
        "7": {"class_type": "ModelPatchTorchSettings", "inputs": {"model": ["6", 0], "enable_fp16_accumulation": True}},
        "8": {"class_type": "LoraLoaderInt8ConvRot", "inputs": {"model": ["7", 0], "lora_name": "minimax_h3_fl2v_lightx2v_turbo_4step_v0.1_comfy_int8convrot.safetensors", "strength_model": 1.0}},
        "9": {"class_type": "MiniMaxChunkFeedForward", "inputs": {"model": ["8", 0], "chunks": 2, "seq_threshold": 4096}},
        "10": {"class_type": "MiniMaxLowVRAMAttention", "inputs": {"model": ["9", 0], "head_chunks": 5}},
        "11": {"class_type": "MiniMaxH3BlockCacheT8", "inputs": {"model": ["10", 0], "residual_diff_threshold": 0.12, "start_percent": 0.08, "end_percent": 0.95, "max_consecutive_hits": 2, "cache_device": "cpu", "metric_stride": 8, "verbose": False}},
        "12": {"class_type": "MiniMaxH3ImageToVideo", "inputs": {
            "clip": ["3", 0], "vae": ["1", 0],
            "first_frame": first_frame_ref,
            "prompt": prompt,
            "width": width, "height": height, "length": length
        }},
        "13": {"class_type": "BasicGuider", "inputs": {"model": ["11", 0], "conditioning": ["12", 0]}},
        "14": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "res_multistep"}},
        "15": {"class_type": "BasicScheduler", "inputs": {"model": ["11", 0], "scheduler": "simple", "steps": 4, "denoise": 1.0}},
        "16": {"class_type": "RandomNoise", "inputs": {"noise_seed": 42 + seed_offset * 7919}},
        "17": {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["16", 0], "guider": ["13", 0], "sampler": ["14", 0], "sigmas": ["15", 0], "latent_image": ["12", 1]}},
        "18": {"class_type": "VAEDecode", "inputs": {"samples": ["17", 0], "vae": ["1", 0]}},
        "19": {"class_type": "VAEDecodeAudio", "inputs": {"samples": ["17", 0], "vae": ["2", 0]}},
        "20": {"class_type": "CreateVideo", "inputs": {"images": ["18", 0], "audio": ["19", 0], "fps": FPS, "bit_depth": 8}},
        "21": {"class_type": "SaveVideo", "inputs": {"video": ["20", 0], "filename_prefix": "video/pipeline-seg%d" % seed_offset, "format": "auto", "codec": "auto"}},
    }


def run_pipeline(server, image_prompt, video_prompts, output_dir="./output", ffmpeg_path="ffmpeg"):
    os.makedirs(output_dir, exist_ok=True)
    n = len(video_prompts)
    print("=" * 50)
    print("Pipeline: 1 image + %d segments x 5s = ~%ds" % (n, n * 5))
    print("Server:", server)
    print("=" * 50)

    print("\n[1] Generating image (%dx%d)..." % IMAGE_SIZE)
    wf = build_zimage_workflow(image_prompt)
    pid = submit_workflow(server, wf)
    files = wait_for_completion(server, pid)
    img_name = files[0]["filename"]
    img_local = os.path.join(output_dir, "pipeline-image.png")
    download_file(server, img_name, files[0].get("subfolder", ""), img_local)
    upload_file(server, img_local, "pipeline-image.png")
    print("  OK: %s" % img_local)

    video_locals = []
    for i in range(n):
        print("\n[%d] Segment %d/%d..." % (i + 2, i + 1, n))
        wf = build_h3_workflow(None, video_prompts[i], i)
        if i == 0:
            wf["4"] = {"class_type": "LoadImage", "inputs": {"image": "pipeline-image.png"}}
            wf["12"]["inputs"]["first_frame"] = ["4", 0]
        else:
            prev_video = video_locals[i - 1]
            last_frame_png = os.path.join(output_dir, "pipeline-frame-%d.png" % i)
            print("  Extracting last frame from seg %d..." % (i - 1))
            extract_last_frame(prev_video, last_frame_png)
            upload_name = "pipeline-frame-%d.png" % i
            upload_file(server, last_frame_png, upload_name)
            wf["4"] = {"class_type": "LoadImage", "inputs": {"image": upload_name}}
            wf["12"]["inputs"]["first_frame"] = ["4", 0]
        pid = submit_workflow(server, wf)
        files = wait_for_completion(server, pid)
        vid = files[0]
        local = os.path.join(output_dir, "pipeline-seg%d.mp4" % i)
        download_file(server, vid["filename"], vid.get("subfolder", ""), local)
        video_locals.append(local)
        print("  OK: %s" % local)
        interrupt(server)
        time.sleep(3)

    print("\n[%d] Concatenating %d segments..." % (n + 2, n))
    concat = os.path.join(output_dir, "concat.txt")
    with open(concat, "w") as f:
        for v in video_locals:
            f.write("file '%s'\n" % v.replace("\\", "/"))
    final = os.path.join(output_dir, "pipeline-final.mp4")
    cmd = [ffmpeg_path, "-f", "concat", "-safe", "0", "-i", concat, "-c", "copy", "-y", final]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("  FFmpeg error:", r.stderr[:500])
        raise Exception("FFmpeg failed")
    sz = os.path.getsize(final)
    print("  OK: %s (%.1f MB)" % (final, sz / 1024 / 1024))
    print("\n" + "=" * 50)
    print("PIPELINE COMPLETE - %d segments, ~%ds total" % (n, n * 5))
    print("=" * 50)
    return final


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ComfyUI Multi-Segment Video Pipeline")
    parser.add_argument("--server", default=DEFAULT_SERVER, help="ComfyUI server URL")
    parser.add_argument("--image-prompt", required=True, help="Prompt for keyframe image")
    parser.add_argument("--prompts", nargs="+", required=True, help="Video segment prompts")
    parser.add_argument("--output", default="./output", help="Output directory")
    parser.add_argument("--ffmpeg", default="ffmpeg", help="Path to ffmpeg")
    args = parser.parse_args()
    run_pipeline(server=args.server, image_prompt=args.image_prompt, video_prompts=args.prompts, output_dir=args.output, ffmpeg_path=args.ffmpeg)
