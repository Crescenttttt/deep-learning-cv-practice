# 深度学习在目标检测中的应用

> 成都信息工程大学（CUIT）「基于深度学习的计算机视觉实践项目」课程作业
> 计科 231–234 班 · 2026 春季学期 W11–W18 · 授课教师：汪曼青

## 选题

**深度学习在目标检测中的应用 —— 国内外研究综述 与 YOLOv10 深度分析**

- 方向：目标检测（Object Detection）
- 深度分析对象：**YOLOv10**（NeurIPS 2024，清华 THU-MIG）
- 技术路线：基于 YOLOv10 官方实现做迁移微调 + 对比/消融实验

## 仓库结构

| 路径 | 内容 |
|------|------|
| `docs/` | 项目文档：完成路径与学习指南、4 篇文献总结（综述导读 + 单篇） |
| `papers/` | 文献库：4 篇 2023+ 目标检测代表论文（PDF + 选篇说明） |
| `presentation/` | 开题报告 PPT、口播稿、PPT 生成脚本 |
| `CLAUDE.md` | 项目背景与协作说明 |
| `开题报告及文献分析要求.pptx` | 课程要求原始文件 |
| `深度学习在CV中的应用.pdf` | 课程参考资料 |

## 文献库（papers/）

| 篇 | 论文 | 路线 | 发表 | 文献总结 |
|----|------|------|------|----------|
| 01 | YOLOv9 — Programmable Gradient Information | CNN · 单阶段 | ECCV 2024 | [01](docs/文献总结-01-YOLOv9.md) |
| 02 | YOLOv10 — Real-Time End-to-End Detection | CNN · 端到端 | NeurIPS 2024 | [02 深度分析](docs/文献总结-02-YOLOv10（深度分析）.md) |
| 03 | RT-DETR — DETRs Beat YOLOs | Transformer · 实时 | CVPR 2024 | [03](docs/文献总结-03-RT-DETR.md) |
| 04 | YOLO-World — Open-Vocabulary Detection | 多模态 · 开放词汇 | CVPR 2024 | [04](docs/文献总结-04-YOLO-World.md) |

四篇的横向对比与选篇逻辑见 [`docs/文献总结-00-综述导读.md`](docs/文献总结-00-综述导读.md)。

## 进度

对齐课程 W11–W18，详见 [`docs/项目完成路径与学习指南.md`](docs/项目完成路径与学习指南.md)。

- [x] W11 调研选题
- [x] W12 开题报告
- [ ] W13–14 需求分析
- [ ] W15–16 概要设计
- [ ] W17–18 模型调试
- [ ] W18 总结汇报

## 协作约定

`main` 分支受保护，所有改动通过 **Pull Request** 合并，建议 squash 合并。
