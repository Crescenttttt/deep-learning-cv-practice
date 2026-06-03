#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""批量推理并画框出图，用于报告插图 / 演示（对应任务 2.3.3 / 3.5.2）。

默认从 test 集随机抽 N 张推理；也可用 --source 指定单图或目录。
结果保存在 runs/detect/<name>/。

用法：
    python scripts/predict_demo.py --weights runs/detect/s_base_640/weights/best.pt
    python scripts/predict_demo.py --weights .../best.pt --n 20 --conf 0.3
    python scripts/predict_demo.py --weights .../best.pt --source path/to/img_or_dir
"""
import argparse
import random
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def main() -> int:
    p = argparse.ArgumentParser(description="YOLOv10 批量推理出图")
    p.add_argument("--weights", required=True)
    p.add_argument("--source", default=None, help="单图/目录；缺省则从 test 集随机抽样")
    p.add_argument("--test-dir", default="datasets/tt100k/images/test", help="随机抽样来源")
    p.add_argument("--n", type=int, default=10, help="随机抽样张数（仅 --source 缺省时生效）")
    p.add_argument("--conf", type=float, default=0.25, help="置信度阈值")
    p.add_argument("--imgsz", type=int, default=640)
    p.add_argument("--device", default="0")
    p.add_argument("--name", default="predict_demo", help="输出到 runs/detect/<name>")
    p.add_argument("--seed", type=int, default=0)
    args = p.parse_args()

    if args.source is not None:
        source = args.source
    else:
        imgs = sorted(Path(args.test_dir).glob("*.jpg"))
        if not imgs:
            print(f"[ERROR] {args.test_dir} 下没有图像，请先跑数据准备脚本", file=sys.stderr)
            return 1
        source = [str(p) for p in random.Random(args.seed).sample(imgs, min(args.n, len(imgs)))]

    from ultralytics import YOLOv10

    model = YOLOv10(args.weights)
    results = model.predict(
        source=source, conf=args.conf, imgsz=args.imgsz, device=args.device,
        save=True, project="runs/detect", name=args.name,
    )
    print(f"\n出图 {len(results)} 张，保存在 {results[0].save_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
