# 电子书工作流详细指南

## 概述

从 PDF/EPUB/MOBI 电子书中提取页面，自动识别内容页，生成做旧+标注素材。

## 完整流程（三阶段）

### 阶段1：扫描+选页（prepare_book.py）

```bash
python3 scripts/prepare_book.py \
  --ebook "path/to/book.pdf" \
  --book-name "英语的基本规律" \
  --pages 3
```

**扫描逻辑：**
- 文本PDF：用 pymupdf 提取文字，`char_count > 100` 判定为内容页
- 扫描PDF：用像素密度分析（`content_ratio > 0.03`），但准确率有限
- 扫描PDF无法自动识别页类型时，输出扫描图片让 Hermes agent 用 vision_analyze 识别

**选页去重：**
- `page_tracker.py` 维护 `.used_pages_{book_key}.json`
- 每次自动跳过已用页
- 所有页用完后自动重置

### 阶段2：视觉分析（Hermes agent）

对 `_raw/` 中的每张内页调用 vision_analyze：

```
vision_analyze("path/to/page.png", "读取页面内容，提取核心知识点...")
```

**关键规则：**
- key_text 必须是页面上实际存在的原文，一字不差
- 不能编造页面上没有的内容
- annotation 基于实际内容写（必考！、核心！等）

保存 JSON 到 `analysis/` 目录。

### 阶段3：生成（pipeline.py --skip-vision）

```bash
python3 scripts/pipeline.py --skip-vision --output-dir "output_dir" --book-name "书名"
```

## 扫描版PDF特殊处理

扫描版PDF（无文字层）的 pymupdf `get_text()` 返回空字符串。

**识别方法：** 提取前几页，检查 `text_length == 0` 且所有页都一样 → 扫描版

**处理流程：**
1. 先提取前12-15页到 `_scan/` 目录
2. 用 vision_analyze 逐页判断类型（封面/版权/前言/目录/正文/练习）
3. 确认正文起始页后，用 `--content-pages "7,8,9"` 参数重新运行 prepare_book.py

**示例：**
```bash
# 第一次：扫描识别
python3 scripts/prepare_book.py --ebook "book.pdf" --scan-range 12
# 输出：所有页都是 IMAGE/BLANK → 需要 vision_analyze

# Hermes agent 用 vision_analyze 识别前12页类型
# 确认：1=封面, 2=扉页, 3=版权, 4=前言, 5-6=目录, 7+=正文

# 第二次：指定内容页
python3 scripts/prepare_book.py --ebook "book.pdf" --content-pages "7,8,9" --pages 3
```

## 踩坑记录

| 坑 | 原因 | 解决 |
|---|---|---|
| 扫描PDF文本提取全为空 | 无文字层 | 用像素密度+vision_analyze |
| 选了目录/前言页当内容 | 没识别页类型 | 先扫描再选 |
| 分析数据是编的 | 没读真实页面 | 必须vision_analyze读实际内容 |
| 同一本书重复用同几页 | 没追踪 | page_tracker.json自动去重 |
| pipeline跑全部20页 | ebook提取默认max_pages=20 | --skip-vision模式只处理有JSON的页 |

## 文件结构

```
{书名}_{时间戳}/
├── _raw/              # 提取的原始页面（临时）
│   ├── 封面.png
│   ├── 7.png
│   └── ...
├── _scan/             # 扫描预览（临时）
├── analysis/          # 视觉分析JSON
│   ├── 7.json
│   └── ...
├── 7.png              # 做旧+标注后的页面
├── cover.png          # 做旧封面
├── 图文描述.txt
└── .used_pages_*.json # 已用页记录（在父目录）
```
