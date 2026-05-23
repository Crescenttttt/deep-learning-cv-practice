# 文献总结 01 · YOLOv9

> **标题**：YOLOv9: Learning What You Want to Learn Using Programmable Gradient Information
> **作者**：Chien-Yao Wang, I-Hau Yeh, Hong-Yuan Mark Liao（台湾中研院 / 台北科技大学）
> **发表**：ECCV 2024 ｜ arXiv [2402.13616](https://arxiv.org/abs/2402.13616)（2024-02）
> **代码**：https://github.com/WongKinYiu/yolov9
> **对应文件**：`papers/01_YOLOv9_Wang_ECCV2024.pdf`

---

## 一、研究什么问题

深度网络在「逐层前向传播」时会不断丢失输入信息，这一现象称为**信息瓶颈（Information Bottleneck）**。
信息一旦丢失，由损失函数反传回来的**梯度就不可靠**，网络会在数据与目标之间建立错误关联，导致预测出错。
这个问题在**小模型 / 轻量模型**上尤其严重——它们参数少，本就「欠参数化」，丢不起信息。

已有的缓解手段各有短板：

- **可逆架构**：显式保留输入信息，但推理时要额外的层来重复输入数据，**推理成本大增**（最高 +2 倍）。
- **掩码建模（masked modeling）**：重建损失常与目标损失冲突。
- **深度监督**：只对超深网络有效，用在轻量模型上会「欠参数化」反而变差。

---

## 二、核心贡献

### 1. PGI（Programmable Gradient Information，可编程梯度信息）

一种新的**辅助监督框架**，由三部分组成：

| 组件 | 作用 | 是否参与推理 |
|------|------|------------|
| 主分支（main branch） | 真正用于推理的网络 | ✅ |
| 辅助可逆分支（auxiliary reversible branch） | 生成可靠梯度，回传给主分支 | ❌ 推理时移除 |
| 多层级辅助信息（multi-level auxiliary information） | 整合各预测头的梯度，缓解深度监督的误差累积 | ❌ 推理时移除 |

**关键点**：辅助分支只在训练时存在，推理时整个移除——所以 **PGI 不增加任何推理开销**。
它把「可逆」当作获取可靠梯度的手段，而非推理时的硬约束，因此**也能用在浅层 / 轻量模型**上（突破了深度监督的限制）。

### 2. GELAN（Generalized ELAN，广义高效层聚合网络）

一种基于**梯度路径规划**设计的新主干结构，融合了 CSPNet 与 ELAN 两种架构的思想。
最大特点：**可以使用任意计算块（computational block）**——用户能针对不同推理设备自由替换基本单元。
结论：GELAN **只用常规卷积**，参数利用率就超过了那些用 depth-wise 卷积的 SOTA 方法。

> YOLOv9 = GELAN（架构）+ PGI（训练）。

---

## 三、数据集与训练设置

- **数据集**：MS COCO 2017（标准目标检测基准）。
- **训练策略**：**train-from-scratch（从零训练）**，不依赖 ImageNet 预训练。
- **训练轮数**：500 epochs。
- **学习率**：前 3 个 epoch 线性 warm-up，之后按模型规模设置衰减。
- **数据增广**：最后 15 个 epoch 关闭 mosaic 增广。
- 网络上用带 planned RepConv 的 CSP 块替换 ELAN，得到 GELAN；辅助损失沿用 YOLOv7 的 auxiliary head 设置。

---

## 四、主要实验结果（MS COCO val）

| 模型 | 参数量(M) | FLOPs(G) | AP(%) |
|------|----------|----------|-------|
| YOLOv9-S | 7.1 | 26.4 | 46.8 |
| YOLOv9-M | 20.0 | 76.3 | 51.4 |
| YOLOv9-C | 25.3 | 102.1 | 53.0 |
| YOLOv9-E | 57.3 | 189.0 | 55.6 |

- 对比 **YOLOv8**：YOLOv9 在参数 **−49%**、计算量 **−43%** 的同时，AP 仍 **+0.6%**。
- 对比轻量/中量级 YOLO-MS：参数少约 10%、计算量少 5~15%，AP 仍高 0.4~0.6%。
- 对比 YOLOv7-AF：YOLOv9-C 参数 −42%、计算量 −22%，AP 持平（53%）。
- 用常规卷积的 YOLOv9，参数利用率甚至超过用 ImageNet 大数据集预训练的 RT-DETR。

---

## 五、消融实验要点

| 表 | 验证内容 | 结论 |
|----|---------|------|
| Table 2 | 不同计算块（Conv / Res / Dark / CSP） | CSP 块综合最优，AP +0.7% |
| Table 3 | GELAN 的 ELAN / CSP 深度组合 | 深度 ≥2 后性能与参数呈线性关系，**对深度不敏感**——结构可自由组合 |
| Table 4 | PGI 用于 backbone / neck | 用 ICN（可逆分支）能稳定提升 |
| Table 5 | 深度监督（DS） vs PGI，跨模型规模 | 深度监督在浅层模型上**掉点**；PGI 在所有规模上都**提升**精度 |

PGI 带来两个核心价值：① 让辅助监督**也适用于浅层模型**；② 让深层模型训练时获得**更可靠的梯度**。

---

## 六、与本组选题的关系

- YOLOv9 是 CNN 路线**紧挨 YOLOv10 的前一代**，写综述时作为「演进背景」一篇。
- PGI 偏理论（信息瓶颈、可逆函数推导），讲解门槛较高，**不建议作为深度分析对象**——本组深度分析选 YOLOv10。
- 注意 YOLOv9 与 YOLOv10 **作者不同团队**（YOLOv9 中研院团队，YOLOv10 清华 THU-MIG），二者是并行的 2024 年成果，不是同一脉络的「续作」。
