#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""每类 AP 柱状图 + CSV（对应任务 3.5.3）。

在指定 split 上跑一次 val（顺带生成混淆矩阵 / PR 曲线到 runs/detect/<name>/），
然后把每类 AP@0.5、AP@0.5:0.95 与 GT 实例数导出为 CSV 和柱状图 PNG。

用法：
    python scripts/plot_per_class_ap.py --weights runs/detect/s_1280_sgd_e150/weights/best.pt --imgsz 1280
"""
import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).parent))
from eval import load_for_eval  # noqa: E402


def count_gt_instances(labels_dir: Path) -> Counter:
    """统计 GT 标签里每个 class_id 的实例数。"""
    counter = Counter()
    for txt in labels_dir.glob("*.txt"):
        for line in txt.read_text().splitlines():
            if line.strip():
                counter[int(line.split()[0])] += 1
    return counter


def main() -> int:
    p = argparse.ArgumentParser(description="每类 AP 柱状图 + CSV")
    p.add_argument("--weights", required=True)
    p.add_argument("--data", default="datasets/tt100k/tt100k.yaml")
    p.add_argument("--split", default="test", choices=["train", "val", "test"])
    p.add_argument("--imgsz", type=int, default=640, help="须与训练时一致")
    p.add_argument("--labels-dir", default=None, help="GT 标签目录，缺省按 split 推断")
    p.add_argument("--out-dir", default="docs/figures", help="柱状图/CSV 输出目录")
    p.add_argument("--name", default="per_class_ap", help="val 输出 runs/detect/<name>，也是图/CSV 文件名前缀")
    p.add_argument("--device", default="0")
    args = p.parse_args()

    model = load_for_eval(args.weights)
    metrics = model.val(data=args.data, split=args.split, imgsz=args.imgsz,
                        device=args.device, project="runs/detect", name=args.name)
    box = metrics.box
    names = model.names

    # box.ap50/box.ap 只含「有 GT 的类」，用 ap_class_index 映射回 class_id
    ap50 = {c: a for c, a in zip(box.ap_class_index, box.ap50)}
    ap = {c: a for c, a in zip(box.ap_class_index, box.ap)}
    labels_dir = Path(args.labels_dir or f"datasets/tt100k/labels/{args.split}")
    gt_counts = count_gt_instances(labels_dir)

    rows = sorted(
        ((names[c], ap50.get(c, 0.0), ap.get(c, 0.0), gt_counts.get(c, 0)) for c in names),
        key=lambda r: r[1],
    )

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / f"{args.name}.csv"
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["class", "AP@0.5", "AP@0.5:0.95", f"GT实例数({args.split})"])
        w.writerows(rows)

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
    plt.rcParams["axes.unicode_minus"] = False

    cls, ap50_v = [r[0] for r in rows], [r[1] for r in rows]
    colors = ["#d62728" if v < 0.5 else "#ff7f0e" if v < 0.7 else "#2ca02c" for v in ap50_v]
    fig, ax = plt.subplots(figsize=(9, 12))
    ax.barh(cls, ap50_v, color=colors)
    for i, (v, n_gt) in enumerate(zip(ap50_v, (r[3] for r in rows))):
        ax.text(v + 0.005, i, f"{v:.2f} (n={n_gt})", va="center", fontsize=7)
    ax.axvline(box.map50, ls="--", c="gray", lw=1, label=f"mAP@0.5={box.map50:.3f}")
    ax.set_xlabel("AP@0.5")
    ax.set_title(f"每类 AP@0.5（{args.split} 集，升序；红<0.5 橙<0.7 绿≥0.7）")
    ax.set_xlim(0, 1.05)
    ax.legend(loc="lower right")
    fig.tight_layout()
    png_path = out_dir / f"{args.name}.png"
    fig.savefig(png_path, dpi=150)

    print(f"\nmAP@0.5={box.map50:.4f}  mAP@0.5:0.95={box.map:.4f}")
    print(f"CSV  -> {csv_path}\n柱状图 -> {png_path}")
    print(f"混淆矩阵/PR 曲线 -> {metrics.save_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
