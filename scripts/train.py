#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""YOLOv10 在 TT100K 上微调训练（对应任务 2.3.1 / 3.1 / 3.2）。

薄封装 ultralytics 的 `model.train()`，加载 COCO 预训练权重后在 TT100K 子集上 fine-tune。
结果统一输出到 `runs/detect/<name>/`，并请在 `experiments.md` 登记（任务 2.3.5）。

用法：
    conda activate yolov10
    # 主实验 baseline（YOLOv10-S，640，100 轮）
    python scripts/train.py --model yolov10s --name s_base_640 --epochs 100 --batch 16
    # 调参：高分辨率
    python scripts/train.py --model yolov10s --name s_imgsz800 --imgsz 800 --batch 8
    # 对比 baseline：YOLOv8-S（任务 3.3）
    python scripts/train.py --model yolov8s.pt --name v8s_base_640 --epochs 100

注：首次会下载预训练权重（HuggingFace），网络受限时先设代理：
    $env:HTTP_PROXY="http://localhost:7897"; $env:HTTPS_PROXY="http://localhost:7897"
"""
import argparse
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def load_model(model: str):
    """支持三种 --model 写法：本地权重文件 / HF 仓库 id / 简写(yolov10s)。"""
    from ultralytics import YOLO, YOLOv10

    if Path(model).exists():            # 本地 .pt / .yaml
        # 按检测头类型选类，而非看文件名：续训的 last.pt 路径不含 "yolov10"，
        # 看文件名会被误判成 YOLOv8 导致续训失败。.yaml 走 except 回退到文件名。
        try:
            import torch
            ckpt = torch.load(model, map_location="cpu", weights_only=False)
            obj = ckpt["model"] if isinstance(ckpt, dict) and "model" in ckpt else ckpt
            head = type(obj.model[-1]).__name__ if hasattr(obj, "model") else ""
            return YOLOv10(model) if "v10" in head.lower() else YOLO(model)
        except Exception:
            return YOLOv10(model) if "yolov10" in model.lower() else YOLO(model)
    if model.startswith("yolov8"):      # YOLOv8 走通用 YOLO（对比实验用）
        return YOLO(model if model.endswith(".pt") else f"{model}.pt")
    if "/" in model:                    # 完整 HF id，如 jameslahm/yolov10s
        return YOLOv10.from_pretrained(model)
    return YOLOv10.from_pretrained(f"jameslahm/{model}")  # 简写 yolov10s -> jameslahm/yolov10s


def main() -> int:
    p = argparse.ArgumentParser(description="YOLOv10 / YOLOv8 在 TT100K 上训练")
    p.add_argument("--model", default="yolov10s", help="预训练权重：本地路径 / HF id / 简写(yolov10s/yolov8s.pt)")
    p.add_argument("--data", default="datasets/tt100k/tt100k.yaml", help="数据集 yaml")
    p.add_argument("--name", required=True, help="实验名（输出到 runs/detect/<name>），请同步登记 experiments.md")
    p.add_argument("--epochs", type=int, default=100)
    p.add_argument("--imgsz", type=int, default=640)
    p.add_argument("--batch", type=int, default=16)
    p.add_argument("--lr0", type=float, default=0.01, help="初始学习率（调参实验 3.2.1）")
    p.add_argument("--optimizer", default="auto",
                   help="优化器：auto/SGD/AdamW（auto 会用 AdamW 并覆盖 lr0≈2e-4，"
                        "要让 --lr0 生效需显式指定 SGD，见 experiments.md baseline 发现）")
    p.add_argument("--close-mosaic", type=int, default=10, help="最后 N 轮关闭 mosaic（论文常见做法，3.2.3）")
    p.add_argument("--device", default="0", help="GPU 编号，或 'cpu'")
    p.add_argument("--workers", type=int, default=8, help="DataLoader worker 数（Windows 高分辨率易崩，调小如 4/2）")
    p.add_argument("--resume", action="store_true", help="从上次中断处续训")
    args = p.parse_args()

    model = load_model(args.model)
    model.train(
        data=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        lr0=args.lr0,
        optimizer=args.optimizer,
        close_mosaic=args.close_mosaic,
        device=args.device,
        workers=args.workers,
        project="runs/detect",  # 固定输出到本仓库内（否则会落到 ultralytics 全局 runs_dir）
        name=args.name,
        resume=args.resume,
    )
    print(f"\n训练完成，结果在 runs/detect/{args.name}/（best.pt 用于 eval.py）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
