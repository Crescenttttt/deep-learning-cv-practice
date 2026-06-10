#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""多实验训练曲线对比图（对应任务 3.5.1）。

读取各 runs/detect/<name>/results.csv，把 val mAP@0.5 随 epoch 的曲线画在一张图上，
直观呈现「auto 欠拟合 vs 显式 SGD」「640 vs 1280」的收敛差异。

用法：
    python scripts/plot_curves.py
    python scripts/plot_curves.py --runs s_base_640 s_640_sgd --out docs/figures/curves_640.png
"""
import argparse
import csv
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DEFAULT_RUNS = ["s_base_640", "s_640_sgd", "s_imgsz1280", "s_1280_sgd_e150", "v8s_base_640"]


def read_map50(results_csv: Path):
    """返回 (epochs, mAP50) 两个列表。results.csv 列名带空格，需 strip。"""
    epochs, map50 = [], []
    with open(results_csv, newline="") as f:
        for row in csv.DictReader(f):
            row = {k.strip(): v for k, v in row.items()}
            epochs.append(int(float(row["epoch"])))
            map50.append(float(row["metrics/mAP50(B)"]))
    return epochs, map50


def main() -> int:
    p = argparse.ArgumentParser(description="训练曲线对比图")
    p.add_argument("--runs", nargs="+", default=DEFAULT_RUNS, help="runs/detect 下的实验名")
    p.add_argument("--out", default="docs/figures/training_curves.png")
    args = p.parse_args()

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
    plt.rcParams["axes.unicode_minus"] = False

    fig, ax = plt.subplots(figsize=(9, 6))
    for name in args.runs:
        csv_path = Path("runs/detect") / name / "results.csv"
        if not csv_path.exists():
            print(f"[WARN] 跳过 {name}：{csv_path} 不存在", file=sys.stderr)
            continue
        epochs, map50 = read_map50(csv_path)
        best_i = max(range(len(map50)), key=map50.__getitem__)
        (line,) = ax.plot(epochs, map50, lw=1.5,
                          label=f"{name}（峰值 {map50[best_i]:.3f} @e{epochs[best_i]}）")
        ax.plot(epochs[best_i], map50[best_i], "o", ms=5, color=line.get_color())

    ax.set_xlabel("epoch")
    ax.set_ylabel("val mAP@0.5")
    ax.set_title("各实验 val mAP@0.5 收敛曲线对比")
    ax.grid(alpha=0.3)
    ax.legend(loc="lower right", fontsize=9)
    fig.tight_layout()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150)
    print(f"曲线图 -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
