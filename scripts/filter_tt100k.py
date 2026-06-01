#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""统计 TT100K 各类别实例数，按阈值筛出子集类别（对应任务 2.2.3 / 需求分析 1.1.2-1.1.3）。

TT100K 200+ 类中多数类样本 < 100，业界通用做法是只取实例数 >= 100 的类（约 45 类）训练。
本脚本不硬编码类别，而是**从标注里统计**后按阈值筛选，从而为"为什么裁剪"提供数据论证。

输入：TT100K 标注 JSON，结构假定为
    {
      "imgs": { "<id>": { "path": "train/<id>.jpg",
                          "objects": [ {"category": "pl80",
                                        "bbox": {"xmin":..,"ymin":..,"xmax":..,"ymax":..}}, ... ] } },
      "types": [ "i1", "i10", ... ]            # 全部类别名（可选）
    }

输出：
    - <out>            选中类别列表，每行一个类名（按字母序，行号即 YOLO class_id），供转换脚本使用
    - <stats-out>      全部类别的实例数 CSV（category,count,selected），供需求分析报告画直方图

用法：
    python scripts/filter_tt100k.py --ann D:/data/TT100K/annotations.json
    python scripts/filter_tt100k.py --ann ... --min-count 100 --out scripts/tt100k_classes.txt
"""
import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):  # 避免中文输出在 Windows 控制台乱码
    sys.stdout.reconfigure(encoding="utf-8")

# 原论文 ">=100 实例" 得到的标准 45 类，仅用于和本次统计结果交叉核对（不参与筛选逻辑）。
REFERENCE_45 = {
    "i2", "i4", "i5", "il100", "il60", "il80", "io", "ip",
    "p10", "p11", "p12", "p19", "p23", "p26", "p27", "p3", "p5", "p6",
    "pg", "ph4", "ph4.5", "ph5", "pl100", "pl120", "pl20", "pl30", "pl40",
    "pl5", "pl50", "pl60", "pl70", "pl80", "pm20", "pm30", "pm55",
    "pn", "pne", "po", "pr40", "w13", "w32", "w55", "w57", "w59", "wo",
}


def count_categories(ann: dict) -> Counter:
    """统计每个类别在全部 imgs 中的实例（bbox）数。"""
    counter = Counter()
    for img in ann["imgs"].values():
        for obj in img.get("objects", []):
            counter[obj["category"]] += 1
    return counter


def main() -> int:
    parser = argparse.ArgumentParser(description="TT100K 类别统计与子集筛选")
    parser.add_argument("--ann", required=True, type=Path, help="TT100K 标注 JSON 路径")
    parser.add_argument("--min-count", type=int, default=100, help="保留类别的最小实例数阈值（默认 100）")
    parser.add_argument("--out", type=Path, default=Path("scripts/tt100k_classes.txt"),
                        help="选中类别列表输出路径")
    parser.add_argument("--stats-out", type=Path, default=Path("scripts/tt100k_class_counts.csv"),
                        help="全类别实例数 CSV 输出路径")
    args = parser.parse_args()

    if not args.ann.is_file():
        print(f"[ERROR] 标注文件不存在: {args.ann}", file=sys.stderr)
        return 1

    with args.ann.open(encoding="utf-8") as f:
        ann = json.load(f)

    counts = count_categories(ann)
    if not counts:
        print("[ERROR] 未统计到任何标注，请检查 JSON 结构是否为 imgs->objects->category", file=sys.stderr)
        return 1

    selected = sorted(c for c, n in counts.items() if n >= args.min_count)
    total_instances = sum(counts.values())
    kept_instances = sum(counts[c] for c in selected)

    # 写选中类别列表（字母序，行号 = class_id）
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(selected) + "\n", encoding="utf-8")

    # 写全类别统计 CSV（按实例数降序，便于报告画直方图）
    sel_set = set(selected)
    with args.stats_out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["category", "count", "selected"])
        for cat, n in counts.most_common():
            writer.writerow([cat, n, int(cat in sel_set)])

    # 终端摘要
    print(f"标注图像数        : {len(ann['imgs'])}")
    print(f"总类别数          : {len(counts)}")
    print(f"总实例数          : {total_instances}")
    print(f"阈值 (>= 实例)    : {args.min_count}")
    print(f"选中类别数        : {len(selected)}")
    print(f"选中后保留实例数  : {kept_instances} ({kept_instances / total_instances:.1%})")
    print(f"稀有类(< 阈值)数  : {len(counts) - len(selected)}")
    print(f"选中类别已写入    : {args.out}")
    print(f"全类别统计已写入  : {args.stats_out}")

    # 与标准 45 类交叉核对，差异时提示（不报错，供人工判断）
    sel_set = set(selected)
    if sel_set != REFERENCE_45:
        only_ours = sorted(sel_set - REFERENCE_45)
        only_ref = sorted(REFERENCE_45 - sel_set)
        print("\n[提示] 本次筛选结果与论文标准 45 类存在差异（不同标注版本/阈值口径可能导致）：")
        if only_ours:
            print(f"  仅本次有 : {only_ours}")
        if only_ref:
            print(f"  仅标准有 : {only_ref}")
    else:
        print("\n[OK] 筛选结果与论文标准 45 类完全一致。")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
