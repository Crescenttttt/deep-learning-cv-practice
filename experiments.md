# 实验登记表（YOLOv10 + TT100K）

> **用途**：每跑一组训练就在此登记一行，作为报告对比表的数据源（任务 2.3.4 / 2.3.5）。
> **日志规范**：每次训练输出到 `runs/detect/<name>/`，`<name>` 与下表「实验名」一致；
> 训练用 `scripts/train.py`，评测用 `scripts/eval.py --weights runs/detect/<name>/weights/best.pt`。
> 数据集固定：TT100K 45 类，train/val/test = 5493 / 610 / 3067（见 `docs/数据下载与目录说明.md`）。

## 计划实验（待跑，结果列填实测值）

| 实验名 | 模型 | imgsz | batch | lr0 | epochs | 增广 | mAP@0.5 | mAP@0.5:0.95 | 备注 |
|--------|------|:---:|:---:|:---:|:---:|------|:---:|:---:|------|
| `s_base_640` | YOLOv10-S | 640 | 16 | 0.01 | 100 | 默认(mosaic+关10轮) | — | — | **主实验 baseline**（任务 3.1） |
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
| — | — | — | — | — | — | （跑完一组填一行） |

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
