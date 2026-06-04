#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""NMS-free 消融：对比 YOLOv10 「无 NMS(one2one)」vs「带 NMS(one2many)」（任务 3.4.1）。

YOLOv10 的 v10Detect 头联合训练两支：
  - one2one ：一对一标签分配，推理只做 top-k 选择，**无需 NMS**（默认路径）；
  - one2many：传统密集头，推理需要 **标准 NMS** 后处理。
两支共享主干、同一份权重，因此切换推理路径就是公平的 NMS 消融。
本脚本对同一权重跑两遍 test 集评测，打印 mAP 与各阶段延迟（NMS 主要影响 postprocess）。

用法：
    python scripts/ablation_nms.py --weights runs/detect/s_imgsz1280/weights/best.pt --imgsz 1280
"""
import argparse
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def main() -> int:
    p = argparse.ArgumentParser(description="YOLOv10 NMS-free 消融（one2one vs one2many+NMS）")
    p.add_argument("--weights", required=True, help="训练好的权重，如 runs/detect/s_imgsz1280/weights/best.pt")
    p.add_argument("--data", default="datasets/tt100k/tt100k.yaml")
    p.add_argument("--split", default="test", choices=["train", "val", "test"])
    p.add_argument("--imgsz", type=int, default=1280, help="须与训练时一致")
    p.add_argument("--device", default="0")
    args = p.parse_args()

    from ultralytics import YOLOv10
    from ultralytics.models.yolo.detect import DetectionValidator
    import ultralytics.models.yolov10.val as v10val

    # 默认 postprocess 走 one2one（无 NMS）。这里准备一个走 one2many + 标准 NMS 的替身。
    free_postprocess = v10val.YOLOv10DetectionValidator.postprocess

    def nms_postprocess(self, preds):
        if isinstance(preds, dict):
            preds = preds["one2many"]          # 改取传统密集头输出
        return DetectionValidator.postprocess(self, preds)  # 复用 v8 风格 NMS

    def run(tag: str):
        model = YOLOv10(args.weights)
        m = model.val(data=args.data, split=args.split, imgsz=args.imgsz,
                      device=args.device, project="runs/detect", name=f"ablation_nms_{tag}")
        return m

    # ① 无 NMS（YOLOv10 默认）
    m_free = run("free")
    # ② 带 NMS（monkey-patch 后处理为 one2many + NMS，跑完恢复）
    v10val.YOLOv10DetectionValidator.postprocess = nms_postprocess
    try:
        m_nms = run("withnms")
    finally:
        v10val.YOLOv10DetectionValidator.postprocess = free_postprocess

    def row(tag, m):
        s = m.speed  # dict: preprocess / inference / postprocess / (loss)，单位 ms/图
        total = s.get("preprocess", 0) + s.get("inference", 0) + s.get("postprocess", 0)
        return (f"{tag:<14} {m.box.map50:.4f}      {m.box.map:.4f}        "
                f"{s.get('inference', 0):.2f}        {s.get('postprocess', 0):.2f}       {total:.2f}")

    print("\n================ NMS-free 消融对比（test 集）================")
    print(f"{'路径':<14} {'mAP@0.5':<10} {'mAP@.5:.95':<12} {'推理ms':<10} {'后处理ms':<10} {'总ms':<8}")
    print(row("无NMS(one2one)", m_free))
    print(row("带NMS(one2many)", m_nms))
    print("\n注：mAP 接近说明 one2one 头精度无损；后处理(postprocess)延迟差即去掉 NMS 的收益。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
