#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""失败案例挖掘（对应任务 3.5.4）。

对 test 集逐图推理，与 GT 按「同类 + IoU≥0.5」贪心匹配，统计每图漏检(FN)/误检(FP)，
导出最差 top-K 张标注图（绿=检对，红粗=漏检，橙=误检）和汇总 CSV，便于报告写失败分析。

用法：
    python scripts/find_failure_cases.py --weights runs/detect/s_1280_sgd_e150/weights/best.pt --imgsz 1280
"""
import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def load_gt(txt: Path, w: int, h: int):
    """读 YOLO 标签 -> [(cls, x1, y1, x2, y2), ...]（像素坐标）。"""
    boxes = []
    if txt.exists():
        for line in txt.read_text().splitlines():
            if not line.strip():
                continue
            c, cx, cy, bw, bh = line.split()
            cx, cy, bw, bh = float(cx) * w, float(cy) * h, float(bw) * w, float(bh) * h
            boxes.append((int(c), cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2))
    return boxes


def iou(a, b):
    ix1, iy1 = max(a[0], b[0]), max(a[1], b[1])
    ix2, iy2 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
    area_a = (a[2] - a[0]) * (a[3] - a[1])
    area_b = (b[2] - b[0]) * (b[3] - b[1])
    return inter / (area_a + area_b - inter + 1e-9)


def match(gts, preds, iou_thr=0.5):
    """同类贪心匹配（按置信度降序）。返回 (matched_pred_idx, fn_gt_idx, fp_pred_idx)。"""
    used_gt, matched, fp = set(), set(), []
    for pi in sorted(range(len(preds)), key=lambda i: -preds[i][5]):
        best_gi, best_iou = -1, iou_thr
        for gi, g in enumerate(gts):
            if gi in used_gt or g[0] != preds[pi][0]:
                continue
            v = iou(g[1:], preds[pi][1:5])
            if v >= best_iou:
                best_gi, best_iou = gi, v
        if best_gi >= 0:
            used_gt.add(best_gi)
            matched.add(pi)
        else:
            fp.append(pi)
    fn = [gi for gi in range(len(gts)) if gi not in used_gt]
    return matched, fn, fp


def main() -> int:
    p = argparse.ArgumentParser(description="失败案例挖掘")
    p.add_argument("--weights", required=True)
    p.add_argument("--images-dir", default="datasets/tt100k/images/test")
    p.add_argument("--labels-dir", default="datasets/tt100k/labels/test")
    p.add_argument("--imgsz", type=int, default=640, help="须与训练时一致")
    p.add_argument("--conf", type=float, default=0.25)
    p.add_argument("--top", type=int, default=12, help="导出最差 K 张标注图")
    p.add_argument("--out-dir", default="runs/analysis/failure_cases")
    p.add_argument("--device", default="0")
    args = p.parse_args()

    import cv2
    from ultralytics import YOLOv10

    model = YOLOv10(args.weights)
    names = model.names
    n_imgs = len(list(Path(args.images_dir).glob("*.jpg")))
    print(f"扫描 {n_imgs} 张 test 图……")

    records, fn_by_cls, fp_by_cls = [], Counter(), Counter()
    # 传目录而非路径 list：list 会被当成单个 batch 整体堆叠，3067 张直接 OOM
    for r in model.predict(source=args.images_dir, conf=args.conf,
                           imgsz=args.imgsz, device=args.device, stream=True, verbose=False):
        h, w = r.orig_shape
        img_path = Path(r.path)
        gts = load_gt(Path(args.labels_dir) / f"{img_path.stem}.txt", w, h)
        preds = [(int(c), *xyxy, float(cf)) for c, xyxy, cf in
                 zip(r.boxes.cls.tolist(), r.boxes.xyxy.tolist(), r.boxes.conf.tolist())]
        matched, fn, fp = match(gts, preds)
        for gi in fn:
            fn_by_cls[names[gts[gi][0]]] += 1
        for pi in fp:
            fp_by_cls[names[preds[pi][0]]] += 1
        records.append((img_path, gts, preds, matched, fn, fp))

    total_fn, total_fp = sum(fn_by_cls.values()), sum(fp_by_cls.values())
    print(f"\n总计漏检 FN={total_fn}，误检 FP={total_fp}（conf≥{args.conf}, IoU≥0.5）")
    print("漏检最多的类：", fn_by_cls.most_common(10))
    print("误检最多的类：", fp_by_cls.most_common(10))

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "summary.csv", "w", newline="", encoding="utf-8-sig") as f:
        w_ = csv.writer(f)
        w_.writerow(["image", "GT数", "漏检FN", "误检FP", "漏检类", "误检类"])
        for img_path, gts, preds, _, fn, fp in sorted(records, key=lambda x: -(len(x[4]) + len(x[5]))):
            w_.writerow([img_path.name, len(gts), len(fn), len(fp),
                         " ".join(names[gts[gi][0]] for gi in fn),
                         " ".join(names[preds[pi][0]] for pi in fp)])

    worst = sorted(records, key=lambda x: -(len(x[4]) + len(x[5])))[: args.top]
    for rank, (img_path, gts, preds, matched, fn, fp) in enumerate(worst, 1):
        img = cv2.imread(str(img_path))
        for pi in matched:
            x1, y1, x2, y2 = map(int, preds[pi][1:5])
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 200, 0), 2)
        for gi in fn:
            c, x1, y1, x2, y2 = gts[gi][0], *map(int, gts[gi][1:])
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 4)
            cv2.putText(img, f"MISS:{names[c]}", (x1, max(0, y1 - 8)),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
        for pi in fp:
            c, x1, y1, x2, y2 = preds[pi][0], *map(int, preds[pi][1:5])
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 165, 255), 3)
            cv2.putText(img, f"FP:{names[c]} {preds[pi][5]:.2f}", (x1, max(0, y1 - 8)),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 165, 255), 2)
        cv2.imwrite(str(out_dir / f"rank{rank:02d}_fn{len(fn)}_fp{len(fp)}_{img_path.name}"), img)

    print(f"\n最差 {len(worst)} 张标注图与 summary.csv -> {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
