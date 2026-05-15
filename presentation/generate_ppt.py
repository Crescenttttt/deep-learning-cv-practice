"""Generate the opening-report PPT.

Modern academic style: warm off-white background, deep slate text,
single teal accent. Clean hierarchy, thin rules, generous whitespace.
"""

from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

# ---------- design tokens ----------
BG       = RGBColor(0xFB, 0xFA, 0xF7)  # off-white paper
INK      = RGBColor(0x0F, 0x17, 0x2A)  # near-black
INK_SOFT = RGBColor(0x33, 0x3D, 0x52)  # softer body text
MUTED    = RGBColor(0x6B, 0x72, 0x80)  # secondary
RULE     = RGBColor(0xD6, 0xD3, 0xCB)  # divider
ACCENT   = RGBColor(0x0F, 0x76, 0x6E)  # deep teal
ACCENT_L = RGBColor(0xCC, 0xE3, 0xE0)  # pale teal fill
CARD_BG  = RGBColor(0xF3, 0xF1, 0xEC)  # subtle card

FONT = "微软雅黑"
FONT_NUM = "Segoe UI"

# ---------- helpers ----------

def set_run_fonts(run, latin=FONT_NUM, ea=FONT):
    rPr = run._r.get_or_add_rPr()
    for tag, face in (("a:latin", latin), ("a:ea", ea), ("a:cs", ea)):
        el = rPr.find(qn(tag))
        if el is None:
            el = etree.SubElement(rPr, qn(tag))
        el.set("typeface", face)


def add_bg(slide, prs):
    rect = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    rect.line.fill.background()
    rect.fill.solid()
    rect.fill.fore_color.rgb = BG
    # send to back
    spTree = rect._element.getparent()
    spTree.remove(rect._element)
    spTree.insert(2, rect._element)
    return rect


def add_text(
    slide, left, top, width, height, text, *,
    size=14, bold=False, color=INK, align="left", anchor="top",
    spacing=1.15, font=FONT, latin=FONT_NUM, letter_space=None,
):
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.margin_left = tf.margin_right = 0
    tf.margin_top = tf.margin_bottom = 0
    tf.word_wrap = True
    tf.vertical_anchor = {"top": MSO_ANCHOR.TOP, "middle": MSO_ANCHOR.MIDDLE, "bottom": MSO_ANCHOR.BOTTOM}[anchor]

    lines = text.split("\n")
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = {"left": PP_ALIGN.LEFT, "center": PP_ALIGN.CENTER, "right": PP_ALIGN.RIGHT}[align]
        p.line_spacing = spacing
        run = p.add_run()
        run.text = line
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.color.rgb = color
        run.font.name = latin
        set_run_fonts(run, latin=latin, ea=font)
        if letter_space is not None:
            rPr = run._r.get_or_add_rPr()
            rPr.set("spc", str(letter_space))
    return tb


def add_rule(slide, left, top, width, *, color=RULE, weight=0.75):
    line = slide.shapes.add_connector(1, left, top, left + width, top)
    line.line.color.rgb = color
    line.line.width = Pt(weight)
    return line


def add_box(slide, left, top, width, height, *, fill=None, line=None, line_w=0.75, radius=False):
    shape_type = MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE
    box = slide.shapes.add_shape(shape_type, left, top, width, height)
    if radius:
        box.adjustments[0] = 0.05
    if fill is None:
        box.fill.background()
    else:
        box.fill.solid()
        box.fill.fore_color.rgb = fill
    if line is None:
        box.line.fill.background()
    else:
        box.line.color.rgb = line
        box.line.width = Pt(line_w)
    box.shadow.inherit = False
    return box


def header(slide, section_label, page_num, total):
    # section label top-left
    add_text(slide, Inches(0.6), Inches(0.42), Inches(6), Inches(0.3),
             section_label.upper(), size=10, color=ACCENT, bold=True, letter_space=200)
    # page number bottom-right
    add_text(slide, Inches(11.6), Inches(7.05), Inches(1.2), Inches(0.3),
             f"{page_num:02d} / {total:02d}", size=9, color=MUTED, align="right")
    # footer left
    add_text(slide, Inches(0.6), Inches(7.05), Inches(8), Inches(0.3),
             "基于深度学习的计算机视觉实践项目  ·  开题报告  ·  目标检测方向",
             size=9, color=MUTED)
    # top rule
    add_rule(slide, Inches(0.6), Inches(0.85), Inches(12.13))


def slide_title(slide, title, sub=None):
    add_text(slide, Inches(0.6), Inches(1.05), Inches(12), Inches(0.7),
             title, size=28, bold=True, color=INK, spacing=1.0)
    if sub:
        add_text(slide, Inches(0.6), Inches(1.75), Inches(12), Inches(0.4),
                 sub, size=13, color=MUTED)


# ---------- presentation ----------

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]

TOTAL = 15

# ===== Slide 1: Cover =====
s = prs.slides.add_slide(BLANK)
add_bg(s, prs)
# big accent vertical bar on left
add_box(s, Inches(0.6), Inches(2.6), Inches(0.06), Inches(2.3), fill=ACCENT)
# eyebrow
add_text(s, Inches(0.85), Inches(2.55), Inches(8), Inches(0.3),
         "OPENING REPORT  ·  2026 SPRING",
         size=10, color=ACCENT, bold=True, letter_space=300)
# main title
add_text(s, Inches(0.85), Inches(2.95), Inches(11.5), Inches(1.4),
         "深度学习在目标检测中的应用",
         size=44, bold=True, color=INK, spacing=1.1)
# subtitle
add_text(s, Inches(0.85), Inches(4.05), Inches(11.5), Inches(0.6),
         "国内外研究综述 与 YOLOv10 深度分析",
         size=20, color=INK_SOFT, spacing=1.1)
# rule
add_rule(s, Inches(0.85), Inches(5.05), Inches(4))
# bottom meta
add_text(s, Inches(0.85), Inches(5.25), Inches(8), Inches(0.3),
         "课程：基于深度学习的计算机视觉实践项目",
         size=12, color=INK_SOFT)
add_text(s, Inches(0.85), Inches(5.6), Inches(8), Inches(0.3),
         "授课教师：汪曼青",
         size=12, color=MUTED)
# right-bottom
add_text(s, Inches(8.5), Inches(6.6), Inches(4.2), Inches(0.3),
         "成都信息工程大学  ·  计科 231–234",
         size=11, color=MUTED, align="right")
add_text(s, Inches(8.5), Inches(6.9), Inches(4.2), Inches(0.3),
         "2026.05",
         size=11, color=MUTED, align="right")
# small marker top-right
add_text(s, Inches(11.5), Inches(0.5), Inches(1.2), Inches(0.3),
         "01 / 15", size=9, color=MUTED, align="right")

# ===== Slide 2: TOC =====
s = prs.slides.add_slide(BLANK)
add_bg(s, prs)
header(s, "目录 · contents", 2, TOTAL)
slide_title(s, "目录", "本次开题汇报的四个核心部分")

toc = [
    ("01", "选题背景与意义", "Background & Motivation"),
    ("02", "国内外研究现状", "4 篇 2023+ 代表性论文"),
    ("03", "YOLOv10 深度分析", "动机 · 框架 · 创新 · 实验"),
    ("04", "技术路线与计划", "Approach & Timeline"),
]
top = Inches(2.55)
gap = Inches(1.05)
for i, (n, zh, en) in enumerate(toc):
    y = top + gap * i
    add_text(s, Inches(0.95), y, Inches(1.0), Inches(0.7),
             n, size=36, bold=True, color=ACCENT, font=FONT_NUM, latin=FONT_NUM)
    add_text(s, Inches(2.1), y + Inches(0.08), Inches(8), Inches(0.5),
             zh, size=22, bold=True, color=INK)
    add_text(s, Inches(2.1), y + Inches(0.6), Inches(8), Inches(0.35),
             en, size=11, color=MUTED, letter_space=200)
    if i < len(toc) - 1:
        add_rule(s, Inches(0.95), y + Inches(0.98), Inches(11.4))

# ===== Slide 3: Background =====
s = prs.slides.add_slide(BLANK)
add_bg(s, prs)
header(s, "01 · 选题背景", 3, TOTAL)
slide_title(s, "选题背景与研究意义", "为什么是目标检测？")

# Left column: definition
left_x = Inches(0.6)
col_w = Inches(5.9)
add_text(s, left_x, Inches(2.3), col_w, Inches(0.35),
         "什么是目标检测", size=13, bold=True, color=ACCENT, letter_space=150)
add_rule(s, left_x, Inches(2.7), col_w)
add_text(s, left_x, Inches(2.85), col_w, Inches(1.5),
         "在图像中同时回答两个问题：\n\n· 「在哪里」 —— 用边界框定位物体\n· 「是什么」 —— 对边界框内物体分类",
         size=14, color=INK_SOFT, spacing=1.5)

# subtask comparison
add_text(s, left_x, Inches(4.6), col_w, Inches(0.35),
         "与相关 CV 任务的关系", size=11, bold=True, color=MUTED, letter_space=150)
tasks = [("分类", "整图 →  单一类别"),
         ("检测", "图中多物体 →  框 + 类别"),
         ("分割", "每个像素 →  类别")]
for i, (k, v) in enumerate(tasks):
    yy = Inches(4.95) + Inches(0.42) * i
    add_text(s, left_x, yy, Inches(0.9), Inches(0.35),
             k, size=12, bold=True, color=INK)
    add_text(s, left_x + Inches(0.9), yy, Inches(5), Inches(0.35),
             v, size=12, color=INK_SOFT)

# Right column: applications
right_x = Inches(6.95)
add_text(s, right_x, Inches(2.3), col_w, Inches(0.35),
         "代表性应用场景", size=13, bold=True, color=ACCENT, letter_space=150)
add_rule(s, right_x, Inches(2.7), col_w)

apps = [
    ("自动驾驶", "实时识别车辆、行人、交通标志"),
    ("智慧安防", "人脸、异常行为、违禁物检测"),
    ("医学影像", "辅助检出病灶、肺结节、息肉"),
    ("工业质检", "缺陷自动定位、装配缺漏检"),
]
for i, (k, v) in enumerate(apps):
    yy = Inches(2.95) + Inches(0.78) * i
    add_box(s, right_x, yy, Inches(0.18), Inches(0.55), fill=ACCENT)
    add_text(s, right_x + Inches(0.4), yy + Inches(0.02), col_w, Inches(0.35),
             k, size=14, bold=True, color=INK)
    add_text(s, right_x + Inches(0.4), yy + Inches(0.32), col_w, Inches(0.3),
             v, size=11, color=MUTED)

# ===== Slide 4: Timeline =====
s = prs.slides.add_slide(BLANK)
add_bg(s, prs)
header(s, "01 · 选题背景", 4, TOTAL)
slide_title(s, "目标检测技术发展脉络", "从两阶段到 Transformer，从闭集到开放词汇")

# timeline horizontal line
ty = Inches(4.6)
add_rule(s, Inches(0.8), ty, Inches(11.7), color=RULE, weight=1.2)

milestones = [
    ("2014", "R-CNN", "两阶段开端"),
    ("2015", "Fast R-CNN\nYOLO v1", "单阶段诞生"),
    ("2017", "Mask R-CNN\nFPN", "多尺度融合"),
    ("2020", "DETR", "Transformer 入局"),
    ("2022", "YOLOv7", "CNN 极致优化"),
    ("2023", "RT-DETR", "实时 Transformer"),
    ("2024", "YOLOv9 / v10\nYOLO-World", "端到端 · 开放词汇"),
]
n = len(milestones)
x0 = Inches(0.8)
total_w = Inches(11.7)
step = total_w / (n - 1)
for i, (year, models, note) in enumerate(milestones):
    cx = x0 + step * i
    # node
    node = s.shapes.add_shape(MSO_SHAPE.OVAL, cx - Emu(60000), ty - Emu(60000),
                              Emu(120000), Emu(120000))
    node.line.color.rgb = ACCENT
    node.line.width = Pt(1.5)
    node.fill.solid()
    node.fill.fore_color.rgb = BG if i < n - 1 else ACCENT
    # year above
    add_text(s, cx - Inches(0.7), ty - Inches(0.55), Inches(1.4), Inches(0.3),
             year, size=11, bold=True, color=ACCENT, align="center", font=FONT_NUM, latin=FONT_NUM)
    # model name below
    add_text(s, cx - Inches(0.9), ty + Inches(0.3), Inches(1.8), Inches(0.8),
             models, size=11, bold=True, color=INK, align="center", spacing=1.2)
    add_text(s, cx - Inches(0.9), ty + Inches(1.05), Inches(1.8), Inches(0.4),
             note, size=10, color=MUTED, align="center", spacing=1.2)

# annotation: where this report focuses
add_box(s, Inches(8.1), Inches(2.5), Inches(4.5), Inches(0.55), fill=ACCENT_L, radius=True)
add_text(s, Inches(8.25), Inches(2.6), Inches(4.3), Inches(0.4),
         "↓  本组聚焦：2023 年以来的 4 项代表性工作",
         size=12, bold=True, color=ACCENT)

# ===== Slides 5-8: papers =====

def paper_slide(slide, idx_label, title_en, title_zh, authors, venue, tag, contributions, key_metric):
    header(slide, f"02 · 文献综述", 4 + int(idx_label), TOTAL)
    # paper number badge
    add_text(slide, Inches(0.6), Inches(1.05), Inches(2), Inches(0.5),
             f"PAPER {idx_label}",
             size=11, bold=True, color=ACCENT, letter_space=300)
    # tag pill
    add_box(slide, Inches(11.1), Inches(1.07), Inches(1.65), Inches(0.4),
            fill=ACCENT_L, radius=True)
    add_text(slide, Inches(11.1), Inches(1.13), Inches(1.65), Inches(0.3),
             tag, size=10, bold=True, color=ACCENT, align="center")
    # title EN
    add_text(slide, Inches(0.6), Inches(1.55), Inches(12), Inches(0.55),
             title_en, size=22, bold=True, color=INK, spacing=1.1)
    # title CN
    add_text(slide, Inches(0.6), Inches(2.18), Inches(12), Inches(0.4),
             title_zh, size=14, color=INK_SOFT)
    # meta
    add_rule(slide, Inches(0.6), Inches(2.78), Inches(12.13))
    add_text(slide, Inches(0.6), Inches(2.9), Inches(8.5), Inches(0.35),
             authors, size=11, color=MUTED)
    add_text(slide, Inches(9.5), Inches(2.9), Inches(3.3), Inches(0.35),
             venue, size=11, color=ACCENT, align="right", bold=True)

    # contributions
    add_text(slide, Inches(0.6), Inches(3.55), Inches(6), Inches(0.35),
             "核心贡献", size=12, bold=True, color=ACCENT, letter_space=150)
    for i, (head, body) in enumerate(contributions):
        yy = Inches(3.95) + Inches(0.95) * i
        add_text(slide, Inches(0.6), yy, Inches(0.35), Inches(0.35),
                 f"{i+1}", size=14, bold=True, color=ACCENT, font=FONT_NUM, latin=FONT_NUM)
        add_text(slide, Inches(1.0), yy, Inches(6.5), Inches(0.35),
                 head, size=14, bold=True, color=INK)
        add_text(slide, Inches(1.0), yy + Inches(0.35), Inches(6.5), Inches(0.55),
                 body, size=11, color=INK_SOFT, spacing=1.4)

    # key metric card
    cx = Inches(7.8); cy = Inches(3.95); cw = Inches(5.0); ch = Inches(2.6)
    add_box(slide, cx, cy, cw, ch, fill=CARD_BG, radius=True)
    add_text(slide, cx + Inches(0.3), cy + Inches(0.2), cw - Inches(0.6), Inches(0.35),
             "关键指标", size=11, bold=True, color=ACCENT, letter_space=150)
    add_rule(slide, cx + Inches(0.3), cy + Inches(0.6), cw - Inches(0.6))
    add_text(slide, cx + Inches(0.3), cy + Inches(0.75), cw - Inches(0.6), ch - Inches(0.8),
             key_metric, size=12, color=INK_SOFT, spacing=1.6)


paper_slide(
    prs.slides.add_slide(BLANK), "01",
    "YOLOv9: Learning What You Want to Learn",
    "通过可编程梯度信息保留输入完整性",
    "Chien-Yao Wang, I-Hau Yeh, Hong-Yuan Mark Liao",
    "ECCV 2024",
    "CNN · 单阶段",
    [
        ("Programmable Gradient Information (PGI)",
         "通过辅助可逆分支保留完整输入信息，缓解深层网络中的信息瓶颈，且不增加推理开销。"),
        ("Generalized ELAN (GELAN)",
         "基于梯度路径规划的轻量主干，仅用常规卷积即在参数效率上超过 depth-wise 主流方法。"),
        ("从零训练即超越预训练 SOTA",
         "在 MS COCO 上从零训练即可超越大多数依赖大规模预训练的检测器。"),
    ],
    "MS COCO test-dev\n\n· YOLOv9-E：55.6 AP@0.5:0.95\n· 参数 57.3M，FLOPs 189G\n· 同精度下参数较 YOLOv8 减少约 16%",
)
# slide 5 added; we used add_slide before paper_slide consumed it
# Adjust: paper_slide takes the slide; we passed prs.slides.add_slide so it's just made

paper_slide(
    prs.slides.add_slide(BLANK), "02",
    "YOLOv10: Real-Time End-to-End Object Detection",
    "用一致的双重分配实现 NMS-free 端到端",
    "Ao Wang, Hui Chen, et al. (THU-MIG)",
    "NeurIPS 2024",
    "CNN · 端到端",
    [
        ("Consistent Dual Assignments",
         "训练阶段一对多分配获丰富监督，推理阶段一对一分配实现 NMS-free 端到端部署。"),
        ("Holistic Efficiency-Accuracy Design",
         "轻量分类头、空间-通道解耦下采样、Rank-guided block，全局协同优化效率与精度。"),
        ("速度与参数全面占优",
         "S 型号比 RT-DETR-R18 快 1.8×；B 型号比 YOLOv9-C 延迟降 46%、参数减 25%。"),
    ],
    "MS COCO val\n\n· YOLOv10-S：46.3 AP / 2.49 ms\n· YOLOv10-L：53.2 AP\n· 无需 NMS 后处理，可端到端部署",
)

paper_slide(
    prs.slides.add_slide(BLANK), "03",
    "DETRs Beat YOLOs on Real-time Object Detection",
    "首个进入实时区间的 Transformer 检测器（RT-DETR）",
    "Yian Zhao, Wenyu Lv, et al. (Baidu)",
    "CVPR 2024",
    "Transformer · 实时",
    [
        ("Efficient Hybrid Encoder",
         "解耦尺度内自注意力与跨尺度融合，大幅降低多尺度编码的计算开销。"),
        ("Uncertainty-minimal Query Selection",
         "用「分类与定位不确定性最低」的特征初始化 object query，加速收敛。"),
        ("可调速推理",
         "无需重新训练即可通过调整解码层数在精度与 FPS 间灵活权衡。"),
    ],
    "MS COCO val · T4 GPU\n\n· RT-DETR-R50：53.1 AP / 108 FPS\n· RT-DETR-R101：54.3 AP / 74 FPS\n· 速度精度同步超过同期 YOLO 系列",
)

paper_slide(
    prs.slides.add_slide(BLANK), "04",
    "YOLO-World: Real-Time Open-Vocabulary Detection",
    "把 CLIP 思想引入 YOLO，实现实时开放词汇检测",
    "Tianheng Cheng, Lin Song, et al. (HUST × Tencent)",
    "CVPR 2024",
    "多模态 · 开放词汇",
    [
        ("RepVL-PAN",
         "可重参数化的视觉-语言路径聚合网络，让文本嵌入与多尺度视觉特征深度交互。"),
        ("Region-Text Contrastive Learning",
         "在 CC3M、Objects365、GoldG 等大规模图文数据上做区域级对比学习预训练。"),
        ("部署友好的文本嵌入离线化",
         "推理时文本编码可离线缓存，几乎不增加在线推理负担。"),
    ],
    "LVIS · V100\n\n· 35.4 AP / 52.0 FPS（zero-shot）\n· 支持任意文本提示\n· 可平滑迁移到下游分割任务",
)

# ===== Slide 9: comparison =====
s = prs.slides.add_slide(BLANK)
add_bg(s, prs)
header(s, "02 · 文献综述", 9, TOTAL)
slide_title(s, "四篇文献综合对比", "两条技术路线 × 两个时间断面，形成清晰演进矩阵")

# Build a table manually using shapes (looks cleaner than default table)
col_titles = ["", "技术路线", "核心创新", "端到端", "代表速度", "适用方向"]
rows = [
    ["YOLOv9 (ECCV'24)",   "CNN 单阶段",     "PGI + GELAN",          "否（需 NMS）", "—",            "通用 · 精度优先"],
    ["YOLOv10 (NeurIPS'24)","CNN 单阶段",    "双重分配 + 效率设计",   "是",          "S：2.49 ms",   "通用 · 实时部署"],
    ["RT-DETR (CVPR'24)",  "Transformer",   "混合编码 + 不确定性查询", "是",          "R50：108 FPS", "通用 · 实时高精度"],
    ["YOLO-World (CVPR'24)","多模态 (V+L)",  "RepVL-PAN + 图文对比",   "是",          "52 FPS",       "开放词汇 · 零样本"],
]

table_left = Inches(0.6)
table_top = Inches(2.4)
table_w = Inches(12.13)
n_cols = len(col_titles)
col_widths = [Inches(2.7), Inches(1.9), Inches(2.8), Inches(1.5), Inches(1.5), Inches(1.73)]
header_h = Inches(0.5)
row_h = Inches(0.75)

# header row
x = table_left
for i, t in enumerate(col_titles):
    add_text(s, x + Inches(0.1), table_top + Inches(0.12), col_widths[i] - Inches(0.1), Inches(0.35),
             t, size=11, bold=True, color=ACCENT, letter_space=150)
    x += col_widths[i]
add_rule(s, table_left, table_top + header_h, table_w, color=INK, weight=1.0)

# data rows
for ri, row in enumerate(rows):
    ry = table_top + header_h + row_h * ri
    x = table_left
    for ci, cell in enumerate(row):
        if ci == 0:
            add_text(s, x + Inches(0.1), ry + Inches(0.22), col_widths[ci] - Inches(0.1), Inches(0.35),
                     cell, size=12, bold=True, color=INK)
        else:
            add_text(s, x + Inches(0.1), ry + Inches(0.22), col_widths[ci] - Inches(0.1), Inches(0.35),
                     cell, size=11, color=INK_SOFT)
        x += col_widths[ci]
    add_rule(s, table_left, ry + row_h, table_w)

# bottom annotation
add_text(s, Inches(0.6), Inches(6.3), Inches(12), Inches(0.4),
         "→  四篇互相引用、对比明确，构成「CNN ↔ Transformer × 闭集 ↔ 开放」的演进矩阵。",
         size=12, color=ACCENT, bold=True)
add_text(s, Inches(0.6), Inches(6.7), Inches(12), Inches(0.3),
         "我们选择 YOLOv10 作为深度分析对象 —— 创新点清晰、消融完整、官方代码可复现度高。",
         size=11, color=MUTED)

# ===== Slide 10: YOLOv10 motivation & framework =====
s = prs.slides.add_slide(BLANK)
add_bg(s, prs)
header(s, "03 · YOLOv10 深度分析", 10, TOTAL)
slide_title(s, "YOLOv10：动机与整体框架",
            "在 YOLOv8 / v9 已逼近精度天花板的前提下，瓶颈在哪里？")

# Three pain points (top half)
pains = [
    ("01", "NMS 拖累端到端",  "训练阶段一对多分配带来重复预测，\n推理必须依赖 NMS 后处理，难以端到端部署。"),
    ("02", "结构存在效率冗余", "分类头与回归头计算不平衡，\n常规下采样与堆叠 block 存在显式冗余。"),
    ("03", "精度–延迟两难",   "提精度通常带来延迟和参数膨胀，\n缺乏在两者之间协同优化的全局视角。"),
]
for i, (n, h, b) in enumerate(pains):
    x = Inches(0.6 + 4.25 * i)
    add_box(s, x, Inches(2.4), Inches(4.05), Inches(1.85), fill=CARD_BG, radius=True)
    add_text(s, x + Inches(0.3), Inches(2.55), Inches(0.6), Inches(0.4),
             n, size=18, bold=True, color=ACCENT, font=FONT_NUM, latin=FONT_NUM)
    add_text(s, x + Inches(1.0), Inches(2.6), Inches(2.9), Inches(0.4),
             h, size=14, bold=True, color=INK)
    add_text(s, x + Inches(0.3), Inches(3.15), Inches(3.5), Inches(1.0),
             b, size=11, color=INK_SOFT, spacing=1.5)

# framework diagram (bottom half)
add_text(s, Inches(0.6), Inches(4.65), Inches(12), Inches(0.35),
         "整体架构（沿用 YOLO 经典三段式，做了多处效率重写）",
         size=11, bold=True, color=ACCENT, letter_space=150)
add_rule(s, Inches(0.6), Inches(5.0), Inches(12.13))

# pipeline
boxes = [
    ("Input\n640×640", BG, INK, RULE),
    ("Backbone\n(CSP + Rank-Guided Block)", ACCENT_L, INK, ACCENT),
    ("Neck\n(SCDown + PAN)", ACCENT_L, INK, ACCENT),
    ("Dual Heads\n(One-to-Many ‖ One-to-One)", ACCENT, BG, ACCENT),
    ("Predictions\n(NMS-free)", BG, INK, RULE),
]
bx_y = Inches(5.4)
bx_w = Inches(2.25)
bx_h = Inches(1.15)
gap_x = Inches(0.2)
total_box_w = bx_w * 5 + gap_x * 4
start_x = (prs.slide_width - total_box_w) / 2
for i, (label, fill, txt_c, line_c) in enumerate(boxes):
    bx = start_x + (bx_w + gap_x) * i
    add_box(s, bx, bx_y, bx_w, bx_h, fill=fill, line=line_c, line_w=1.0, radius=True)
    add_text(s, bx, bx_y, bx_w, bx_h,
             label, size=12, bold=True, color=txt_c, align="center", anchor="middle", spacing=1.3)
    if i < len(boxes) - 1:
        ax = bx + bx_w + Emu(20000)
        ay = bx_y + bx_h / 2
        arrow = s.shapes.add_connector(1, ax, ay, ax + gap_x - Emu(40000), ay)
        arrow.line.color.rgb = MUTED
        arrow.line.width = Pt(1.2)

# ===== Slide 11: YOLOv10 innovations =====
s = prs.slides.add_slide(BLANK)
add_bg(s, prs)
header(s, "03 · YOLOv10 深度分析", 11, TOTAL)
slide_title(s, "YOLOv10：两大核心创新",
            "Consistent Dual Assignments  ＋  Holistic Efficiency-Accuracy Design")

# Left card
lx = Inches(0.6); lw = Inches(5.95)
add_box(s, lx, Inches(2.4), lw, Inches(4.3), fill=CARD_BG, radius=True)
add_text(s, lx + Inches(0.4), Inches(2.55), lw - Inches(0.6), Inches(0.4),
         "① 一致性双重分配",
         size=16, bold=True, color=ACCENT)
add_text(s, lx + Inches(0.4), Inches(2.95), lw - Inches(0.6), Inches(0.4),
         "Consistent Dual Assignments  ·  解决「NMS 依赖」",
         size=10, color=MUTED, letter_space=100)
add_rule(s, lx + Inches(0.4), Inches(3.42), lw - Inches(0.8), color=ACCENT)

l_items = [
    ("训练分支：一对多",
     "保留 YOLO 经典的丰富监督信号，让每个目标被多个 anchor 学习，加快收敛。"),
    ("推理分支：一对一",
     "去除重复预测，单一最优匹配，省去 NMS 后处理。"),
    ("一致性匹配度量",
     "用同一度量对齐两支头的目标函数，避免「训练–推理鸿沟」。"),
]
for i, (h, b) in enumerate(l_items):
    yy = Inches(3.6) + Inches(1.05) * i
    add_text(s, lx + Inches(0.4), yy, Inches(0.4), Inches(0.35),
             "·", size=18, bold=True, color=ACCENT)
    add_text(s, lx + Inches(0.7), yy + Inches(0.02), lw - Inches(0.9), Inches(0.4),
             h, size=13, bold=True, color=INK)
    add_text(s, lx + Inches(0.7), yy + Inches(0.38), lw - Inches(0.9), Inches(0.7),
             b, size=11, color=INK_SOFT, spacing=1.4)

# Right card
rx = Inches(6.78); rw = Inches(5.95)
add_box(s, rx, Inches(2.4), rw, Inches(4.3), fill=CARD_BG, radius=True)
add_text(s, rx + Inches(0.4), Inches(2.55), rw - Inches(0.6), Inches(0.4),
         "② 效率–精度协同设计",
         size=16, bold=True, color=ACCENT)
add_text(s, rx + Inches(0.4), Inches(2.95), rw - Inches(0.6), Inches(0.4),
         "Holistic Design  ·  解决「结构冗余 + 精度延迟两难」",
         size=10, color=MUTED, letter_space=100)
add_rule(s, rx + Inches(0.4), Inches(3.42), rw - Inches(0.8), color=ACCENT)

r_items = [
    ("轻量分类头",
     "削减分类头参数与算力，对最终精度影响极小，但显著降延迟。"),
    ("空间–通道解耦下采样 (SCDown)",
     "把传统下采样拆分为两步，保留信息同时降运算。"),
    ("Rank-Guided Block",
     "按特征图的内在秩自适应选择更紧凑的 block。"),
    ("大核 + 部分自注意力",
     "在关键阶段引入大核卷积与轻量自注意力，提升精度而不显著增加延迟。"),
]
for i, (h, b) in enumerate(r_items):
    yy = Inches(3.55) + Inches(0.78) * i
    add_text(s, rx + Inches(0.4), yy, Inches(0.4), Inches(0.35),
             "·", size=18, bold=True, color=ACCENT)
    add_text(s, rx + Inches(0.7), yy + Inches(0.02), rw - Inches(0.9), Inches(0.4),
             h, size=12, bold=True, color=INK)
    add_text(s, rx + Inches(0.7), yy + Inches(0.34), rw - Inches(0.9), Inches(0.45),
             b, size=10, color=INK_SOFT, spacing=1.35)

# ===== Slide 12: YOLOv10 results =====
s = prs.slides.add_slide(BLANK)
add_bg(s, prs)
header(s, "03 · YOLOv10 深度分析", 12, TOTAL)
slide_title(s, "YOLOv10：实验结果与消融",
            "MS COCO  ·  Tesla T4 GPU  ·  TensorRT FP16")

# left: main comparison table
add_text(s, Inches(0.6), Inches(2.3), Inches(7.5), Inches(0.35),
         "与同规模检测器的对比",
         size=11, bold=True, color=ACCENT, letter_space=150)

cols = ["Model", "Params", "FLOPs", "Latency", "AP@val"]
data = [
    ["YOLOv8-S",   "11.2M", "28.6G", "2.66 ms", "44.9"],
    ["YOLOv9-S",   " 7.2M", "26.7G", "2.66 ms", "46.7"],
    ["RT-DETR-R18","20.0M", "60.0G", "4.58 ms", "46.5"],
    ["YOLOv10-S",  " 7.2M", "21.6G", "2.49 ms", "46.3"],
    ["YOLOv8-L",   "43.7M","165.2G", "8.06 ms", "52.9"],
    ["YOLOv10-L",  "24.4M","120.3G", "7.28 ms", "53.2"],
]
tw = Inches(7.5)
col_w = [Inches(2.1), Inches(1.2), Inches(1.2), Inches(1.5), Inches(1.5)]
tt = Inches(2.7)
hh = Inches(0.4)
rh = Inches(0.45)
# header
x = Inches(0.6)
for i, c in enumerate(cols):
    add_text(s, x + Inches(0.05), tt + Inches(0.05), col_w[i] - Inches(0.1), Inches(0.3),
             c, size=10, bold=True, color=MUTED, letter_space=100)
    x += col_w[i]
add_rule(s, Inches(0.6), tt + hh, tw, color=INK, weight=1.0)
# rows
for ri, row in enumerate(data):
    ry = tt + hh + rh * ri
    x = Inches(0.6)
    is_v10 = "v10" in row[0]
    if is_v10:
        # subtle highlight band
        add_box(s, Inches(0.6), ry, tw, rh, fill=ACCENT_L)
    for ci, cell in enumerate(row):
        c_color = ACCENT if is_v10 and ci == 0 else (INK if ci == 0 else INK_SOFT)
        add_text(s, x + Inches(0.05), ry + Inches(0.1), col_w[ci] - Inches(0.1), Inches(0.3),
                 cell, size=11, bold=(ci == 0), color=c_color, font=FONT_NUM, latin=FONT_NUM)
        x += col_w[ci]
    add_rule(s, Inches(0.6), ry + rh, tw)

# right: takeaways
rx = Inches(8.4); rw = Inches(4.4)
add_text(s, rx, Inches(2.3), rw, Inches(0.35),
         "三点关键结论", size=11, bold=True, color=ACCENT, letter_space=150)
add_rule(s, rx, Inches(2.7), rw)

takeaways = [
    ("精度持平甚至略优",
     "YOLOv10-S 与 YOLOv9-S 精度相当，YOLOv10-L 反超 YOLOv8-L 0.3 AP。"),
    ("延迟显著下降",
     "YOLOv10-S 在 7.2M 参数下，延迟比 RT-DETR-R18 低 45%。"),
    ("消融全面",
     "论文逐项消融了 NMS-free 分支、SCDown、Rank-block 等设计，因果链清晰。"),
]
for i, (h, b) in enumerate(takeaways):
    yy = Inches(2.95) + Inches(1.2) * i
    add_text(s, rx, yy, Inches(0.4), Inches(0.4),
             f"0{i+1}", size=14, bold=True, color=ACCENT, font=FONT_NUM, latin=FONT_NUM)
    add_text(s, rx + Inches(0.6), yy + Inches(0.02), rw - Inches(0.6), Inches(0.4),
             h, size=13, bold=True, color=INK)
    add_text(s, rx + Inches(0.6), yy + Inches(0.4), rw - Inches(0.6), Inches(0.75),
             b, size=10, color=INK_SOFT, spacing=1.4)

# ===== Slide 13: Technical approach =====
s = prs.slides.add_slide(BLANK)
add_bg(s, prs)
header(s, "04 · 技术路线", 13, TOTAL)
slide_title(s, "拟采用技术路线", "在 YOLOv10 官方实现基础上做迁移与对比实验")

steps = [
    ("环境与基线", "搭建 PyTorch + CUDA 环境；clone YOLOv10 官方仓库；\n用 MS COCO 子集跑通预训练权重的推理。"),
    ("数据集准备", "结合实际场景选定数据集（候选：交通标志 TT100K / 安全帽 SHWD / 医学息肉 Kvasir-SEG）。\n划分 train / val / test = 7 / 1.5 / 1.5，转换 YOLO 标注格式。"),
    ("模型微调",   "在自定义数据集上微调 YOLOv10-S / -M，调参（lr、batch、增广策略），追踪 mAP 曲线。"),
    ("对比与消融", "横向对比 YOLOv8 / RT-DETR；纵向消融 NMS-free 分支与 SCDown 的贡献。"),
    ("交付物",     "完整训练日志、对比表、可视化 demo、需求分析与概要设计文档。"),
]
top_y = Inches(2.35)
for i, (h, b) in enumerate(steps):
    yy = top_y + Inches(0.88) * i
    # step number
    add_box(s, Inches(0.6), yy + Inches(0.05), Inches(0.55), Inches(0.55), fill=ACCENT, radius=True)
    add_text(s, Inches(0.6), yy + Inches(0.05), Inches(0.55), Inches(0.55),
             f"{i+1}", size=18, bold=True, color=BG, align="center", anchor="middle",
             font=FONT_NUM, latin=FONT_NUM)
    add_text(s, Inches(1.4), yy, Inches(11), Inches(0.4),
             h, size=15, bold=True, color=INK)
    add_text(s, Inches(1.4), yy + Inches(0.38), Inches(11), Inches(0.5),
             b, size=11, color=INK_SOFT, spacing=1.4)

# ===== Slide 14: Timeline =====
s = prs.slides.add_slide(BLANK)
add_bg(s, prs)
header(s, "04 · 时间规划", 14, TOTAL)
slide_title(s, "项目时间规划", "对齐课程第 11–18 周节奏")

phases = [
    ("W11", "调研选题", 0, 1),
    ("W12", "开题报告", 1, 1),
    ("W13–14", "需求分析", 2, 2),
    ("W15–16", "环境搭建 / 跑通代码", 4, 2),
    ("W17–18", "模型调试 / 对比实验", 6, 2),
    ("W18",   "总结汇报", 7, 1),
]
chart_x = Inches(2.3)
chart_y = Inches(2.7)
chart_w = Inches(10.0)
chart_h = Inches(3.3)
n_weeks = 8
unit = chart_w / n_weeks

# week ticks
for w in range(n_weeks + 1):
    x = chart_x + unit * w
    add_text(s, x - Inches(0.3), chart_y - Inches(0.35), Inches(0.6), Inches(0.3),
             f"W{11 + w}" if w < n_weeks else "",
             size=10, color=MUTED, align="center", font=FONT_NUM, latin=FONT_NUM)
    # vertical guideline
    line = s.shapes.add_connector(1, x, chart_y, x, chart_y + chart_h)
    line.line.color.rgb = RULE
    line.line.width = Pt(0.5)

bar_h = Inches(0.42)
gap_v = Inches(0.52)
for i, (week, label, start, span) in enumerate(phases):
    by = chart_y + Inches(0.1) + gap_v * i
    bx = chart_x + unit * start
    bw = unit * span - Emu(20000)
    add_box(s, bx, by, bw, bar_h, fill=ACCENT, radius=True)
    add_text(s, bx + Inches(0.15), by, bw, bar_h,
             label, size=11, bold=True, color=BG, anchor="middle")
    # row label
    add_text(s, Inches(0.6), by, Inches(1.6), bar_h,
             week, size=11, bold=True, color=INK_SOFT, anchor="middle",
             font=FONT_NUM, latin=FONT_NUM)

# note
add_text(s, Inches(0.6), Inches(6.4), Inches(12), Inches(0.35),
         "当前位置：W11  ·  本周完成调研与开题准备；下周（W12）汇报。",
         size=12, bold=True, color=ACCENT)

# ===== Slide 15: Thanks =====
s = prs.slides.add_slide(BLANK)
add_bg(s, prs)
add_text(s, Inches(0), Inches(2.8), prs.slide_width, Inches(1.5),
         "谢 谢 聆 听",
         size=60, bold=True, color=INK, align="center", letter_space=600)
add_text(s, Inches(0), Inches(4.3), prs.slide_width, Inches(0.5),
         "Questions & Discussion",
         size=16, color=MUTED, align="center", letter_space=300)
add_rule(s, Inches(5.5), Inches(5.1), Inches(2.33), color=ACCENT, weight=1.5)
add_text(s, Inches(0), Inches(5.4), prs.slide_width, Inches(0.4),
         "基于深度学习的计算机视觉实践项目  ·  目标检测方向",
         size=11, color=MUTED, align="center")
add_text(s, Inches(11.6), Inches(7.05), Inches(1.2), Inches(0.3),
         "15 / 15", size=9, color=MUTED, align="right")


# ---------- save ----------
out_path = Path(__file__).parent / "开题报告.pptx"
prs.save(out_path)
print(f"Saved: {out_path} ({out_path.stat().st_size / 1024:.1f} KB)")
print(f"Slides: {len(prs.slides)}")
