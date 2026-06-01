#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把 TT100K 标注转成 Ultralytics/YOLO 数据集（对应任务 2.2.4-2.2.6）。

流程：
  1. 读 filter_tt100k.py 产出的类别列表（行号 = class_id）；
  2. 遍历标注，按官方 path 前缀（train/test）分流，从 train 再切出 val；
  3. 每个目标转 YOLO 行 `class_id cx cy w h`（按各图实际尺寸归一化到 [0,1]）；
  4. 在输出目录建标准 images/{train,val,test} + labels/{train,val,test} 结构；
     图像默认用**硬链接**（同盘零拷贝、无需管理员），失败回退复制；
  5. 生成 Ultralytics 风格 tt100k.yaml。

默认只保留"含至少一个选中类别目标"的图（其余类别的框被丢弃）。

用法：
    python scripts/tt100k_to_yolo.py --data-root D:/data/TT100K
    python scripts/tt100k_to_yolo.py --data-root D:/data/TT100K \
        --classes scripts/tt100k_classes.txt --out datasets/tt100k --val-ratio 0.1
"""
from __future__ import annotations  # 允许 Path|None 等标注在 Python 3.9 上使用

import argparse
import json
import os
import random
import shutil
import sys
from pathlib import Path

from PIL import Image

if hasattr(sys.stdout, "reconfigure"):  # 避免中文输出在 Windows 控制台乱码
    sys.stdout.reconfigure(encoding="utf-8")


def load_classes(path: Path) -> dict:
    """类名 -> class_id（id 即文件中的行序，从 0 开始）。"""
    names = [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    return {name: i for i, name in enumerate(names)}


def find_ann(data_root: Path, ann_arg: Path | None) -> Path:
    if ann_arg is not None:
        return ann_arg
    for cand in ("annotations.json", "annotations_all.json"):
        if (data_root / cand).is_file():
            return data_root / cand
    raise FileNotFoundError(f"在 {data_root} 下未找到 annotations.json / annotations_all.json，请用 --ann 指定")


def split_of(rel_path: str) -> str | None:
    """根据 path 前缀判断官方划分；other/ 等无关图返回 None。"""
    head = rel_path.replace("\\", "/").split("/", 1)[0].lower()
    if head == "train":
        return "train"
    if head == "test":
        return "test"
    return None


def to_yolo_line(cid: int, bbox: dict, w: int, h: int) -> str:
    cx = (bbox["xmin"] + bbox["xmax"]) / 2 / w
    cy = (bbox["ymin"] + bbox["ymax"]) / 2 / h
    bw = (bbox["xmax"] - bbox["xmin"]) / w
    bh = (bbox["ymax"] - bbox["ymin"]) / h
    # 防越界裁剪到 [0,1]
    cx, cy = min(max(cx, 0.0), 1.0), min(max(cy, 0.0), 1.0)
    bw, bh = min(max(bw, 0.0), 1.0), min(max(bh, 0.0), 1.0)
    return f"{cid} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}"


def link_image(src: Path, dst: Path, mode: str) -> None:
    if dst.exists():
        return
    if mode == "hardlink":
        try:
            os.link(src, dst)
            return
        except OSError:
            shutil.copy2(src, dst)  # 跨盘等情况回退
            return
    if mode == "symlink":
        os.symlink(src, dst)
        return
    shutil.copy2(src, dst)


def write_yaml(out: Path, id2name: dict) -> Path:
    yaml_path = out / "tt100k.yaml"
    lines = [
        "# 由 scripts/tt100k_to_yolo.py 自动生成",
        f"path: {out.resolve().as_posix()}",
        "train: images/train",
        "val: images/val",
        "test: images/test",
        "",
        "names:",
    ]
    lines += [f"  {cid}: {name}" for cid, name in sorted(id2name.items())]
    yaml_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return yaml_path


def main() -> int:
    parser = argparse.ArgumentParser(description="TT100K -> YOLO 数据集转换")
    parser.add_argument("--data-root", required=True, type=Path, help="TT100K 根目录（含 train/ test/ 及标注 JSON）")
    parser.add_argument("--ann", type=Path, default=None, help="标注 JSON 路径（默认在 data-root 下自动查找）")
    parser.add_argument("--classes", type=Path, default=Path("scripts/tt100k_classes.txt"),
                        help="filter_tt100k.py 产出的类别列表")
    parser.add_argument("--out", type=Path, default=Path("datasets/tt100k"), help="YOLO 数据集输出目录")
    parser.add_argument("--val-ratio", type=float, default=0.1, help="从官方 train 切出 val 的比例（默认 0.1）")
    parser.add_argument("--seed", type=int, default=0, help="划分随机种子")
    parser.add_argument("--link-mode", choices=["hardlink", "copy", "symlink"], default="hardlink",
                        help="图像放置方式（默认 hardlink 同盘零拷贝）")
    parser.add_argument("--keep-empty", action="store_true", help="保留不含选中类别目标的图（作为负样本）")
    parser.add_argument("--limit", type=int, default=0, help="仅处理前 N 张图（调试用，0 = 全部）")
    args = parser.parse_args()

    name2id = load_classes(args.classes)
    id2name = {i: n for n, i in name2id.items()}
    ann_path = find_ann(args.data_root, args.ann)
    with ann_path.open(encoding="utf-8") as f:
        ann = json.load(f)

    # 收集每张图的 (split, image_path, yolo_lines)
    records = []  # (orig_split, id, img_path, lines)
    missing, skipped_empty = 0, 0
    items = list(ann["imgs"].items())
    if args.limit:
        items = items[: args.limit]

    for _id, img in items:
        rel = img["path"]
        osplit = split_of(rel)
        if osplit is None:
            continue
        img_path = args.data_root / rel
        if not img_path.is_file():
            missing += 1
            continue
        try:
            w, h = Image.open(img_path).size
        except Exception:
            missing += 1
            continue
        lines = [to_yolo_line(name2id[o["category"]], o["bbox"], w, h)
                 for o in img.get("objects", []) if o["category"] in name2id]
        if not lines and not args.keep_empty:
            skipped_empty += 1
            continue
        records.append((osplit, Path(rel).stem, img_path, lines))

    if not records:
        print("[ERROR] 没有可用样本，请检查 data-root / 标注结构 / 类别列表", file=sys.stderr)
        return 1

    # 官方 train 再切 val
    train_pool = [r for r in records if r[0] == "train"]
    test_recs = [r for r in records if r[0] == "test"]
    random.Random(args.seed).shuffle(train_pool)
    n_val = int(len(train_pool) * args.val_ratio)
    val_recs = train_pool[:n_val]
    train_recs = train_pool[n_val:]

    split_map = {"train": train_recs, "val": val_recs, "test": test_recs}
    for split, recs in split_map.items():
        (args.out / "images" / split).mkdir(parents=True, exist_ok=True)
        (args.out / "labels" / split).mkdir(parents=True, exist_ok=True)
        for _osplit, sid, img_path, lines in recs:
            link_image(img_path, args.out / "images" / split / f"{sid}{img_path.suffix}", args.link_mode)
            (args.out / "labels" / split / f"{sid}.txt").write_text(
                ("\n".join(lines) + "\n") if lines else "", encoding="utf-8")

    yaml_path = write_yaml(args.out, id2name)

    print(f"标注文件          : {ann_path}")
    print(f"类别数            : {len(name2id)}")
    print(f"train / val / test: {len(train_recs)} / {len(val_recs)} / {len(test_recs)}")
    print(f"丢弃(无选中目标)  : {skipped_empty}")
    print(f"缺失/损坏图       : {missing}")
    print(f"图像放置方式      : {args.link_mode}")
    print(f"输出目录          : {args.out.resolve()}")
    print(f"数据集配置        : {yaml_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
