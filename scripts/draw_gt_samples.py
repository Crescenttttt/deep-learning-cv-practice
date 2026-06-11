#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""随机抽训练图叠加 GT bbox，肉眼验证标注转换无误（对应任务 2.2.7）。

用法：
    python scripts/draw_gt_samples.py --n 20
"""
import argparse
import random
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).parent))
from find_failure_cases import load_gt  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(description="训练集 GT 标注抽样可视化")
    p.add_argument("--images-dir", default="datasets/tt100k/images/train")
    p.add_argument("--labels-dir", default="datasets/tt100k/labels/train")
    p.add_argument("--data", default="datasets/tt100k/tt100k.yaml")
    p.add_argument("--n", type=int, default=20)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--out-dir", default="runs/analysis/gt_samples")
    args = p.parse_args()

    import cv2
    import yaml

    names = yaml.safe_load(Path(args.data).read_text(encoding="utf-8"))["names"]
    imgs = sorted(Path(args.images_dir).glob("*.jpg"))
    samples = random.Random(args.seed).sample(imgs, min(args.n, len(imgs)))

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for img_path in samples:
        img = cv2.imread(str(img_path))
        h, w = img.shape[:2]
        gts = load_gt(Path(args.labels_dir) / f"{img_path.stem}.txt", w, h)
        for c, x1, y1, x2, y2 in gts:
            x1, y1, x2, y2 = map(int, (x1, y1, x2, y2))
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 200, 0), 3)
            cv2.putText(img, names[c], (x1, max(0, y1 - 8)),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 200, 0), 2)
        cv2.imwrite(str(out_dir / img_path.name), img)
        print(f"{img_path.name}: {len(gts)} 个 GT 框")

    print(f"\n{len(samples)} 张抽样图 -> {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
