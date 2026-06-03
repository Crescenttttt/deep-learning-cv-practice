# 实验登记表（YOLOv10 + TT100K）

> **用途**：每跑一组训练就在此登记一行，作为报告对比表的数据源（任务 2.3.4 / 2.3.5）。
> **日志规范**：每次训练输出到 `runs/detect/<name>/`，`<name>` 与下表「实验名」一致；
> 训练用 `scripts/train.py`，评测用 `scripts/eval.py --weights runs/detect/<name>/weights/best.pt`。
> 数据集固定：TT100K 45 类，train/val/test = 5493 / 610 / 3067（见 `docs/数据下载与目录说明.md`）。

## 计划实验（待跑，结果列填实测值）

| 实验名 | 模型 | imgsz | batch | lr0 | epochs | 增广 | mAP@0.5 | mAP@0.5:0.95 | 备注 |
|--------|------|:---:|:---:|:---:|:---:|------|:---:|:---:|------|
| `s_base_640` | YOLOv10-S | 640 | 16 | auto | 100 | 默认(mosaic+关10轮) | **0.415** | **0.302** | ✅ **主实验 baseline**（test 集），未达 0.70，小目标瓶颈明显 |
| `s_lr005` | YOLOv10-S | 640 | 16 | 0.005 | 100 | 默认 | — | — | 调参：学习率（3.2.1） |
| `s_lr001` | YOLOv10-S | 640 | 16 | 0.001 | 100 | 默认 | — | — | 调参：学习率（3.2.1） |
| `s_imgsz800` | YOLOv10-S | 800 | 8 | 0.01 | 100 | 默认 | — | — | 调参：高分辨率，利好小目标（3.2.2） |
| `s_nomosaic` | YOLOv10-S | 640 | 16 | 0.01 | 100 | 全程关 mosaic | — | — | 调参：增广消融（3.2.3） |
| `v8s_base_640` | YOLOv8-S | 640 | 16 | 0.01 | 100 | 默认 | — | — | **横向对比** baseline（3.3.1） |
| `n_base_640` | YOLOv10-N | 640 | 32 | 0.01 | 100 | 默认 | — | — | （可选）轻量版对照 |

> 及格线（任务 1.3.3，先调研后定）：mAP@0.5 ≥ 0.70。达不到则进入调参循环。
> batch 视 12GB 显存调整：640 通常 16 可行，800 建议降到 8。

## 已完成实验记录

| 日期 | 实验名 | mAP@0.5 | mAP@0.5:0.95 | 参数量 | 延迟(ms) | 结论 / 备注 |
|------|--------|:---:|:---:|:---:|:---:|------|
| 2026-06-02 | `s_base_640` | 0.415 | 0.302 | 8.1M / 25.0 GFLOPs | 4.2 | test 集；mP 0.427 / mR 0.445。弱类全是小尺寸限速/限高标志(pl20/ph5/pm30 AP<0.1)，强类为大图案(il100/pl100 AP>0.55)。**小目标是瓶颈** → 下一步提 imgsz 到 1280 |

### baseline 关键发现
- **未达及格线 0.70**：根因是 640 把 2048² 原图的小标志压没了（TT100K 标志常仅几十像素）。
- **`optimizer=auto` 覆盖了 `--lr0`**：实际用 AdamW lr≈0.0002（偏保守）。要控 lr 需显式 `optimizer=SGD`。
- 改进优先级：① **imgsz 1280**（对小目标最有效，batch 需降到 4）② 显式 SGD + lr=0.01 ③ 关 mosaic 末段微调。

## 复现命令速查

```powershell
conda activate yolov10

# 主实验
python scripts/train.py --model yolov10s --name s_base_640 --epochs 100 --batch 16
python scripts/eval.py  --weights runs/detect/s_base_640/weights/best.pt
python scripts/predict_demo.py --weights runs/detect/s_base_640/weights/best.pt --n 10

# 对比 YOLOv8-S
python scripts/train.py --model yolov8s.pt --name v8s_base_640 --epochs 100 --batch 16
python scripts/eval.py  --weights runs/detect/v8s_base_640/weights/best.pt
```
