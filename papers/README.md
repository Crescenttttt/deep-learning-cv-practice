# 文献库：目标检测（Object Detection），2023+

本目录收录 4 篇 2023 年以来的目标检测代表性论文，用于课程开题报告与文献综述。
选取原则：**两条技术路线 × 两个时间断面**，构成一条清晰的演进线，便于综述写作。

## 选篇逻辑

```
              CNN 系（YOLO 家族）              Transformer 系（DETR 家族）
2023 年节点   ——                              RT-DETR（首个实时 Transformer 检测器）
2024 年节点   YOLOv9 / YOLOv10               YOLO-World（开放词汇 + CNN backbone）
```

- **YOLOv9 / YOLOv10**：CNN 路线的最新两代，分别解决"信息损失"与"NMS 依赖"两个痛点，是工业界的主流基线。
- **RT-DETR**：第一个把 Transformer 检测器拉进实时区间的工作，挑战 YOLO 的速度护城河。
- **YOLO-World**：把视觉–语言预训练（CLIP 思想）引入 YOLO，将检测从"闭集"推到"开放词汇"，是 2024 年的前沿方向。

四篇互相之间有引用与对比关系（YOLOv10 直接对比 RT-DETR；YOLO-World 基于 YOLOv8 backbone），适合写综述时构造"演进 → 对比 → 现状"叙事。

---

## 论文清单

### 1. YOLOv9 — Learning What You Want to Learn Using Programmable Gradient Information

- **文件**：`01_YOLOv9_Wang_ECCV2024.pdf`
- **作者**：Chien-Yao Wang, I-Hau Yeh, Hong-Yuan Mark Liao
- **arXiv**：[2402.13616](https://arxiv.org/abs/2402.13616)（2024-02-21）
- **发表**：ECCV 2024
- **核心问题**：深层网络中信息逐层丢失，导致梯度无法正确指导模型学习。
- **核心贡献**：
  - **PGI（Programmable Gradient Information）**：通过辅助可逆分支，在不增加推理开销的情况下保留完整输入信息。
  - **GELAN**：基于梯度路径规划的轻量主干，只用常规卷积就超过用 depth-wise 的 SOTA。
- **实验**：MS COCO，参数效率与精度均超过 YOLOv7 / YOLOv8。
- **可用作**：CNN 路线主基线 / 复现目标。

### 2. YOLOv10 — Real-Time End-to-End Object Detection

- **文件**：`02_YOLOv10_Wang_NeurIPS2024.pdf`
- **作者**：Ao Wang, Hui Chen, Lihao Liu, Kai Chen, Zijia Lin, Jungong Han, Guiguang Ding（清华 THU-MIG）
- **arXiv**：[2405.14458](https://arxiv.org/abs/2405.14458)（2024-05-23）
- **发表**：NeurIPS 2024
- **核心问题**：YOLO 长期依赖 NMS 做后处理，限制端到端部署；架构存在效率冗余。
- **核心贡献**：
  - **Consistent Dual Assignments**：训练用一对多 / 推理用一对一，实现 NMS-free 端到端。
  - **整体效率–精度协同设计**：轻量分类头、空间–通道解耦下采样、rank-guided block。
- **实验**：YOLOv10-S 比 RT-DETR-R18 快 1.8×；YOLOv10-B 比 YOLOv9-C 延迟降 46%、参数减 25%。
- **可用作**：与 YOLOv9 形成"前后代对比"；提供 NMS-free 视角。

### 3. RT-DETR — DETRs Beat YOLOs on Real-time Object Detection

- **文件**：`03_RT-DETR_Zhao_CVPR2024.pdf`
- **作者**：Yian Zhao, Wenyu Lv, Shangliang Xu, Jinman Wei, Guanzhong Wang, Qingqing Dang, Yi Liu, Jie Chen（百度）
- **arXiv**：[2304.08069](https://arxiv.org/abs/2304.08069)（2023-04-17，v3：2024-04-03）
- **发表**：CVPR 2024
- **核心问题**：DETR 系列精度高但太慢，没法和 YOLO 比实时性能。
- **核心贡献**：
  - **Efficient Hybrid Encoder**：解耦尺度内交互与跨尺度融合，大幅降低多尺度编码开销。
  - **Uncertainty-minimal Query Selection**：用不确定性最低的特征初始化 object query。
  - 灵活调速：可在不重训的前提下调解码层数控制 FPS。
- **实验**：COCO 上 RT-DETR-R50 达到 53.1 AP / 108 FPS（T4 GPU），超过同期 YOLO 系列。
- **可用作**：Transformer 路线对照组；与 YOLO 的"速度–精度"权衡讨论核心。

### 4. YOLO-World — Real-Time Open-Vocabulary Object Detection

- **文件**：`04_YOLO-World_Cheng_CVPR2024.pdf`
- **作者**：Tianheng Cheng, Lin Song, Yixiao Ge, Wenyu Liu, Xinggang Wang, Ying Shan（华科 + 腾讯 ARC Lab）
- **arXiv**：[2401.17270](https://arxiv.org/abs/2401.17270)（2024-01-30）
- **发表**：CVPR 2024
- **核心问题**：经典 YOLO 只能检测预定义类别，不能识别训练集没见过的物体（开放词汇问题）。
- **核心贡献**：
  - **RepVL-PAN**：可重参数化的视觉–语言路径聚合网络，让文本嵌入和视觉特征深度交互。
  - **Region-Text Contrastive Learning**：基于大规模图文数据（CC3M、Objects365、GoldG）做预训练。
  - 推理时文本编码可离线缓存，部署时几乎无额外开销。
- **实验**：LVIS 上 35.4 AP / 52.0 FPS（V100），同时支持 zero-shot 推理与下游分割。
- **可用作**：前沿方向；如果选题涉及"开放场景 / 多类别 / 零样本"则是核心参考。

---

## 推荐"深度分析 1 篇"的候选

按照课程要求要选 1 篇做深度分析（模型框架、数据集划分、参数、训练、评价、消融）。建议优先级：

1. **YOLOv10**（首选）— 结构清晰、消融完整、可复现性高、对比表丰富，适合在 5–8 分钟里讲透。
2. **RT-DETR** — 如果小组想强调 Transformer 路线 / 注意力机制，这篇消融实验做得非常细。
3. **YOLO-World** — 涉及视觉–语言双模态，比另两篇技术栈深，讲解门槛高但出彩。
4. **YOLOv9** — PGI 偏理论（辅助可逆分支），讲清楚需要先讲清梯度信息瓶颈，对新手不友好。

## 下一步建议

- 跑通 YOLOv10 官方仓库（https://github.com/THU-MIG/yolov10）作为基线，对应"概要设计"周。
- 选定具体应用场景（如交通标志检测、口罩检测、医学病灶检测）后，准备对应小数据集做微调。
- 复现路线：YOLOv10 在自定义数据集上微调 → 与 YOLOv8 / RT-DETR 对比 → 写报告。
