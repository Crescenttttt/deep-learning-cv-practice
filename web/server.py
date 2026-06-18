#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""YOLOv10 交通标志检测 — FastAPI 后端。

启动：python server.py [--port 8000] [--weights best.pt]
前端：浏览器打开 http://127.0.0.1:8000
"""
import argparse
import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

import certifi
os.environ["SSL_CERT_FILE"] = certifi.where()

import cv2
import numpy as np
import torch
import uvicorn
from fastapi import FastAPI, File, Form, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from ultralytics import YOLO, YOLOv10
from ultralytics.nn.tasks import YOLOv10DetectionModel

torch.serialization.add_safe_globals([YOLOv10DetectionModel])

# ── 全局 ────────────────────────────────────────────────
MODEL = None
MODEL_PATH = ""
STATIC_DIR = Path(__file__).parent / "static"
RESULTS_DIR = STATIC_DIR / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def load_model(weights: str):
    if not Path(weights).exists():
        raise FileNotFoundError(f"权重文件不存在: {weights}")
    ckpt = torch.load(weights, map_location="cpu", weights_only=False)
    model_obj = ckpt.get("model", ckpt) if isinstance(ckpt, dict) else ckpt
    head_name = type(model_obj.model[-1]).__name__ if hasattr(model_obj, "model") else ""
    return YOLOv10(weights) if "v10" in head_name.lower() else YOLO(weights)


# ── FastAPI ─────────────────────────────────────────────
app = FastAPI(title="Traffic Sign Detection API", docs_url=None, redoc_url=None)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
def startup():
    global MODEL, MODEL_PATH
    MODEL_PATH = os.environ.get("WEIGHTS", "runs/detect/best.pt")
    print(f"Loading model: {MODEL_PATH}")
    MODEL = load_model(MODEL_PATH)
    print(f"Model ready — {len(MODEL.names)} classes")


# ── 工具 ────────────────────────────────────────────────

def _save_annotated(annotated_bgr: np.ndarray, suffix: str = "") -> str:
    """BGR numpy → 存为 JPEG 到 static/results/，返回相对 URL 路径。"""
    stem = f"result_{suffix}" if suffix else "result"
    path = RESULTS_DIR / f"{stem}.jpg"
    cv2.imwrite(str(path), annotated_bgr, [cv2.IMWRITE_JPEG_QUALITY, 92])
    return f"/results/{path.name}"


def _boxes_to_dicts(boxes, names) -> list[dict]:
    """ultralytics Boxes → JSON 友好的列表。"""
    if boxes is None or len(boxes) == 0:
        return []
    out = []
    for box in boxes:
        cls_id = int(box.cls[0])
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        out.append({
            "class": names[cls_id],
            "confidence": round(float(box.conf[0]), 4),
            "bbox": [round(x1), round(y1), round(x2), round(y2)],
        })
    return out


def _get_ffmpeg():
    """查找 ffmpeg 可执行文件，优先系统 PATH，其次 imageio-ffmpeg。"""
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return None


def _optimize_video_for_web(video_path: Path) -> bool:
    """用 ffmpeg 转码为 H.264 + faststart，使浏览器可内联播放。"""
    ffmpeg = _get_ffmpeg()
    if ffmpeg is None:
        return False
    tmp = video_path.with_suffix(".web.mp4")
    try:
        subprocess.run(
            [ffmpeg, "-i", str(video_path),
             "-c:v", "libx264", "-preset", "fast", "-crf", "23",
             "-c:a", "aac", "-b:a", "128k",
             "-movflags", "+faststart", "-y", str(tmp)],
            capture_output=True, check=True, timeout=300,
        )
        tmp.replace(video_path)
        return True
    except Exception:
        if tmp.exists():
            tmp.unlink(missing_ok=True)
        return False


# ── API 端点 ────────────────────────────────────────────

@app.post("/api/detect")
async def detect_image(
    file: UploadFile = File(...),
    conf: float = Form(0.25),
    imgsz: int = Form(1280),
):
    """单张图片检测 → 标注图 + 检测列表 + 统计"""
    if MODEL is None:
        return JSONResponse({"error": "模型未加载"}, status_code=503)

    contents = await file.read()
    img_array = np.frombuffer(contents, np.uint8)
    img_bgr = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    if img_bgr is None:
        return JSONResponse({"error": "无法解码图片"}, status_code=400)

    results = MODEL(img_bgr, conf=conf, imgsz=imgsz, device=0, verbose=False)
    boxes = results[0].boxes
    annotated = results[0].plot()

    url = _save_annotated(annotated)
    detections = _boxes_to_dicts(boxes, MODEL.names)
    seen = len({d["class"] for d in detections})

    return {
        "image_url": url,
        "stats": {"total": len(detections), "classes": seen},
        "detections": detections,
    }


@app.post("/api/detect/batch")
async def detect_batch(
    files: list[UploadFile] = File(...),
    conf: float = Form(0.25),
    imgsz: int = Form(1280),
):
    """批量图片检测 → 多张标注图"""
    if MODEL is None:
        return JSONResponse({"error": "模型未加载"}, status_code=503)

    results_out = []
    for i, f in enumerate(files):
        contents = await f.read()
        img_array = np.frombuffer(contents, np.uint8)
        img_bgr = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        if img_bgr is None:
            results_out.append({"filename": f.filename, "error": "无法解码"})
            continue

        r = MODEL(img_bgr, conf=conf, imgsz=imgsz, device=0, verbose=False)
        boxes = r[0].boxes
        annotated = r[0].plot()
        url = _save_annotated(annotated, str(i))
        detections = _boxes_to_dicts(boxes, MODEL.names)
        results_out.append({
            "filename": f.filename,
            "image_url": url,
            "count": len(detections),
            "detections": detections,
        })

    return {"results": results_out}


@app.post("/api/detect/video")
async def detect_video(
    file: UploadFile = File(...),
    conf: float = Form(0.25),
    imgsz: int = Form(1280),
):
    """视频检测 → 处理后的视频文件路径"""
    if MODEL is None:
        return JSONResponse({"error": "模型未加载"}, status_code=503)

    # 保存上传的视频
    tmp_id = uuid.uuid4().hex[:8]
    tmp_in = RESULTS_DIR / f"_tmp_in_{tmp_id}.mp4"
    tmp_out = RESULTS_DIR / f"video_{tmp_id}.mp4"

    contents = await file.read()
    tmp_in.write_bytes(contents)

    # 用 YOLO 逐帧推理
    results = MODEL.predict(
        source=str(tmp_in), conf=conf, imgsz=imgsz, device=0,
        save=True, stream=True, verbose=False,
        project=str(RESULTS_DIR), name=f"_video_{tmp_id}", exist_ok=True,
    )
    save_dir = None
    for r in results:
        if save_dir is None:
            save_dir = Path(r.save_dir)

    # 清理临时文件
    tmp_in.unlink(missing_ok=True)

    if save_dir is None:
        return JSONResponse({"error": "视频处理失败"}, status_code=500)

    videos = sorted(save_dir.glob("*.mp4")) + sorted(save_dir.glob("*.avi"))
    if not videos:
        return JSONResponse({"error": "未生成输出视频"}, status_code=500)

    # 移到固定位置
    shutil.move(str(videos[0]), str(tmp_out))
    shutil.rmtree(str(save_dir), ignore_errors=True)

    # 优化为 web 可流式播放（MOOV atom → 文件头）
    _optimize_video_for_web(tmp_out)

    return {"video_url": f"/results/video_{tmp_id}.mp4"}


@app.websocket("/ws/detect")
async def ws_detect(ws: WebSocket):
    """实时摄像头检测 — 接收 JPEG 帧，返回检测框 JSON。"""
    await ws.accept()
    if MODEL is None:
        await ws.send_json({"error": "模型未加载"})
        await ws.close()
        return

    conf = 0.25
    imgsz = 640

    try:
        while True:
            msg = await ws.receive()

            if "text" in msg:
                # 配置更新：{"type":"config","conf":0.5,"imgsz":640}
                import json
                try:
                    cfg = json.loads(msg["text"])
                    if cfg.get("type") == "config":
                        conf = float(cfg.get("conf", conf))
                        imgsz = int(cfg.get("imgsz", imgsz))
                except (json.JSONDecodeError, ValueError):
                    pass
                continue

            if "bytes" in msg:
                raw = msg["bytes"]
                img_array = np.frombuffer(raw, np.uint8)
                img_bgr = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                if img_bgr is None:
                    continue

                h, w = img_bgr.shape[:2]
                results = MODEL(img_bgr, conf=conf, imgsz=imgsz, device=0, verbose=False)
                boxes = results[0].boxes

                dets = []
                if boxes is not None and len(boxes) > 0:
                    for box in boxes:
                        cls_id = int(box.cls[0])
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        dets.append({
                            "class": MODEL.names[cls_id],
                            "confidence": round(float(box.conf[0]), 3),
                            "bbox": [round(x1), round(y1), round(x2), round(y2)],
                        })

                await ws.send_json({
                    "detections": dets,
                    "frame_w": w,
                    "frame_h": h,
                })

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await ws.send_json({"error": str(e)})
        except Exception:
            pass


@app.get("/api/model")
def model_info():
    """模型元信息"""
    if MODEL is None:
        return JSONResponse({"error": "模型未加载"}, status_code=503)

    return {
        "weights": MODEL_PATH,
        "num_classes": len(MODEL.names),
        "classes": list(MODEL.names.values()),
    }


# ── 静态文件 ────────────────────────────────────────────
app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")


# ── 入口 ────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser(description="YOLOv10 检测 API 服务")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--weights", default="runs/detect/best.pt")
    args = p.parse_args()

    os.environ["WEIGHTS"] = args.weights
    uvicorn.run("server:app", host="0.0.0.0", port=args.port, reload=False)


if __name__ == "__main__":
    main()
