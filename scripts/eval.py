#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""在 TT100K test 集上评测训练好的模型（对应任务 2.3.2 / 3.1.3）。

输出主指标 mAP@0.5、mAP@0.5:0.95，以及每类 AP（用于报告里的每类 AP 柱状图、找弱类）。

用法：
    python scripts/eval.py --weights runs/detect/s_base_640/weights/best.pt
    python scripts/eval.py --weights .../best.pt --split val --imgsz 800
"""
import argparse
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def main() -> int:
    p = argparse.ArgumentParser(description="YOLOv10 在 TT100K 上评测")
    p.add_argument("--weights", required=True, help="训练得到的权重，如 runs/detect/<name>/weights/best.pt")
    p.add_argument("--data", default="datasets/tt100k/tt100k.yaml")
    p.add_argument("--split", default="test", choices=["train", "val", "test"], help="评测集（默认 test）")
    p.add_argument("--imgsz", type=int, default=640, help="须与训练时一致")
    p.add_argument("--device", default="0")
    args = p.parse_args()

    from ultralytics import YOLOv10

    model = YOLOv10(args.weights)
    metrics = model.val(data=args.data, split=args.split, imgsz=args.imgsz, device=args.device,
                        project="runs/detect", name=f"eval_{args.split}")

    box = metrics.box
    print("\n========== 总体指标 ==========")
    print(f"mAP@0.5      : {box.map50:.4f}")
    print(f"mAP@0.5:0.95 : {box.map:.4f}")
    print(f"mean Precision: {box.mp:.4f}   mean Recall: {box.mr:.4f}")

    # 每类 AP（box.maps 为各类 mAP@0.5:0.95，按 class_id 顺序）
    names = model.names
    print("\n========== 每类 AP@0.5:0.95（升序，便于定位弱类）==========")
    per_class = sorted(
        ((names[i], ap) for i, ap in enumerate(box.maps)),
        key=lambda x: x[1],
    )
    for name, ap in per_class:
        print(f"  {name:<8} {ap:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
