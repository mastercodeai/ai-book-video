# 📚 AI Book Video (ai-book-video)

**AI 图书带货素材生产线** — 一键把新书照片变成旧书翻页短视频素材

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Hermes Skill](https://img.shields.io/badge/Hermes-Skill-blue.svg)](https://hermes-agent.nousresearch.com)

## 这是什么？

这是一个 Hermes Agent 的 skill，用于**自动生成图书带货短视频素材**。

输入几张新书的照片（封面 + 内页），AI 自动完成：
1. **视觉分析** — 识别每页的核心知识点、关键语句位置
2. **AI 做旧** — 把新书照片变成泛黄、有年代感的旧书效果
3. **手写标注** — 自动添加 7 类手写批注（波浪下划线、红色批注、方框、圆圈、边栏笔记、高亮、星号）
4. **封面生成** — 生成手持旧书 + 红色贴纸大字标题的封面图
5. **图文描述** — 自动生成爆款风格的图文描述文案（含话题标签）

输出效果：逼真的「老教材翻页」风格图片，用于视频号/抖音图书带货短视频。

## 效果预览

```
输入：一本全新教材的照片（封面 + 5张内页）
      ↓ AI 处理（约 5-10 分钟）
输出：做旧+标注的 PNG 图片 + 封面 + 图文描述
```

## 生图引擎说明

### 🏆 推荐：CodeProxy gpt-image-2（自测最稳定）

本 skill 使用 **CodeProxy** 平台的 `gpt-image-2` 模型进行图生图（img2img）。

**为什么选 CodeProxy？**
- ✅ **效果最好**：gpt-image-2 是目前做旧+标注效果最逼真的模型
- ✅ **价格便宜**：首充后低至 **5 分钱一张图**
- ✅ **自测稳定**：经过大量测试，是目前最稳定的 gpt-image-2 第三方平台
- ✅ **无需翻墙**：国内可直接访问（需配置代理，详见下方说明）

**注册链接**：https://codeproxy.dev/register?aff=TGR5N8MN

> 💡 强烈推荐使用 CodeProxy。我们测试过多个平台，CodeProxy 是效果和稳定性最好的。

### API 端点

```
POST https://codeproxy.dev/v1/images/edits
模型：gpt-image-2
```

## 快速开始

### 1. 注册 CodeProxy 账号

访问 https://codeproxy.dev/register?aff=TGR5N8MN 注册并充值（首充有优惠）。

### 2. 配置 API Key

```bash
# 复制配置模板
cp assets/.env.example assets/.env

# 编辑 .env，填入你的 API Key
# IMAGE_API_KEY=你的codeprox...# 如果需要代理（国内访问 codeproxy.dev 通常需要）
# HTTPS_PROXY=http://127.0.0.1:7897
```

### 3. 安装依赖

```bash
pip install pillow opencv-python requests numpy
```

### 4. 准备图片

把原始照片放到输入目录：

```
你的工作目录/
├── 封面.jpg        # 文件名含"封面"即可（封面-英语.jpg 也行）
├── 1.jpg           # 内页，数字命名
├── 2.jpg
├── 3.jpg
└── ...
```

**要求**：
- 封面文件名必须包含「封面」二字
- 内页用数字命名（1.jpg, 2.jpg, ...）
- 图片清晰，光线充足，手机拍摄即可

### 5. 运行

在 Hermes Agent 中：

```
帮我处理这些图书素材：[你的工作目录路径]
```

Agent 会自动：
1. 用 vision_analyze 分析每张内页
2. 保存分析结果
3. 运行 pipeline 生成素材

## 详细配置

### 环境变量 (.env)

```bash
# ===== 必须配置 =====

# CodeProxy API（图生图）
IMAGE_API_URL=https://codeproxy.dev
IMAGE_API_KEY=你的codeprox...

# 代理设置（国内访问 codeproxy.dev 通常需要）
HTTPS_PROXY=http://127.0.0.1:7897
HTTP_PROXY=http://127.0.0.1:7897

# ===== 可选配置 =====

# Vision API（页面分析，Hermes 内置 vision_analyze 优先，此项为备选）
# VISION_API_URL=https://api.openai.com/v1
# VISION_API_KEY=sk-you...# VISION_API_URL=https://token-plan-cn.xiaomimimo.com/v1
# VISION_API_KEY=tp-you...```

### 代理配置说明

CodeProxy.dev 在国内访问需要代理。常见代理端口：

| 代理软件 | 端口 |
|---------|------|
| Clash | 7897 |
| V2Ray | 1080 |
| Shadowsocks | 1080 |

如果你的代理端口不同，请修改 `.env` 中的 `HTTPS_PROXY` 和 `HTTP_PROXY`。

## 输入/输出规范

### 输入目录结构

```
输入目录/
├── 封面.jpg          # 书的封面照片
├── 1.jpg             # 第1页内页
├── 2.jpg             # 第2页内页
├── 3.jpg             # 第3页内页
└── ...               # 建议 3-8 张内页
```

**文件命名规则**：
- 封面：文件名必须包含「封面」二字（如 `封面.jpg`、`封面-英语.jpg`、`封面-微积分.jpg`）
- 内页：数字命名（`1.jpg`、`2.jpg`、`3.jpg`...）

### 输出目录结构

```
输出目录/
├── 1.png             # 做旧+标注的内页1
├── 2.png             # 做旧+标注的内页2
├── 3.png             # 做旧+标注的内页3
├── cover.png         # 做旧封面 + 红色贴纸大字标题
└── 图文描述.txt       # 爆款风格图文描述（含话题标签）
```

### 输出命名规则

```
{书名}_{YYYYMMDD}_{两位流水号}/
```

示例：
- `英语句子结构_20260702_01/`
- `微积分教程_20260702_01/`
- `高中物理_20260702_02/`

**规则**：
- 书名自动清理特殊字符，保留中文/英文/数字，最长 20 字
- 日期格式：YYYYMMDD
- 流水号每天重置（01, 02, 03...）
- analysis/ 子目录和 JPG 原图在生成完成后会自动清理

## 标注效果

### 内页标注（7 类）

| 标注类型 | 效果 | 说明 |
|---------|------|------|
| 红色波浪下划线 | ～～～ | 标记最重要句子 |
| 红色手写批注 | 必考！核心！ | 醒目批注 |
| 蓝色方框 | [ ] | 标记章节标题 |
| 红色圆圈 | ○ | 圈出关键术语 |
| 边栏手写笔记 | 公式/定理/重点 | 根据学科定制 |
| 黄色高亮 | ██ | 标记重要短语 |
| 星号/勾号 | ★ ✓ | 标记关键知识点 |

### 学科标注标签

根据 `--subject` 参数自动匹配：

| 学科 | 边栏手写标签示例 |
|------|----------------|
| 英语 | 主语、谓语、宾语、状语、表语、定语 |
| 数学 | 公式、定理、解题关键、易错、步骤1、步骤2 |
| 语文 | 修辞手法、中心思想、关键词、段落大意、写作手法 |
| 文言 | 实词、虚词、古今异义、词类活用、特殊句式 |
| 物理 | 公式、原理、受力分析、解题关键、易错点 |
| 化学 | 反应方程式、实验步骤、注意安全、易错 |
| 通用 | 重点、难点、考点、易错、必背、理解 |

### 做旧风格

- ✅ 适度泛黄、自然光、手机拍照感（明亮可读）
- ❌ 不要太暗、不要浓重滤镜

## 封面设计

### 封面标题规则引擎

封面标题使用智能规则引擎自动生成，根据学科/作者/年份/页面内容动态生成唯一标题。

**7 种标题模式**：

| 模式 | 示例 |
|------|------|
| 代际对比 | 老一辈就是真敢教 |
| 直接断言 | 老书就是敢真教 |
| 观察提问 | 有没有发现老教材把每个题都讲得很透 |
| 个人见证 | 我宣布这本书是我女儿数学开窍的神 |
| 权威+主题 | 钱学森系统思维精髓 |
| 年份+断言 | 1983年出版老书就是敢教真东西 |
| 情感共鸣 | 感觉以前的书才是真的教书育人 |

**智能变量替换**：
- `{subject_short}` — 学科简称
- `{topic_keyword}` — 页面主题关键词
- `{audience}` — 目标读者（小学儿子/女儿/初中生/高中生）
- `{year}` — 出版年份
- `{author}` — 作者名

## 图文描述格式

自动生成的图文描述输出到 `图文描述.txt`，格式规则：

- ✅ 每行都有内容，紧凑排列
- ✅ 引用页面上的真实口诀/知识点
- ❌ 不要有 `*` 号
- ❌ 不要有空行

**描述结构**：
1. 抓人开头（反问/感叹/对比）
2. 书名+年代+作者（强调"绝版""老书"）
3. 核心卖点
4. 实际内容（根据视觉分析列出）
5. 行动号召（"现在很难找""一定要收"）
6. 话题标签

## 命令行参数

### run_batch.py（推荐使用）

```bash
python3 scripts/run_batch.py \
  --output-dir "输出目录路径" \
  --book-name "书名" \
  --author "作者" \
  --subject "学科" \
  --year "出版年份"
```

**参数说明**：
| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `--output-dir` | ✅ | - | 输出目录路径 |
| `--book-name` | ✅ | - | 书名 |
| `--author` | ❌ | 王克谦 | 作者名 |
| `--subject` | ❌ | 英语 | 学科（英语/数学/语文/文言/物理/化学/通用） |
| `--year` | ❌ | 1984 | 出版年份 |

### pipeline.py（完整 pipeline）

```bash
python3 scripts/pipeline.py \
  --book-name "书名" \
  --author "作者" \
  --subject "学科" \
  --year "出版年份" \
  --output-dir "输出目录" \
  --skip-vision  # 如果已有视觉分析结果，跳过分析步骤
```

### prepare_book.py（电子书模式）

```bash
python3 scripts/prepare_book.py \
  --ebook "电子书路径" \
  --book-name "书名" \
  --pages 3  # 提取页数
```

## 使用示例

### 示例 1：处理英语教材照片

```bash
# 1. 准备图片
mkdir -p ~/book-photos
# 把封面.jpg 和 1.jpg, 2.jpg, 3.jpg 放进去

# 2. 运行
python3 scripts/run_batch.py \
  --output-dir "~/book-output/英语句子结构_20260702_01" \
  --book-name "英语句子结构" \
  --author "王克谦" \
  --subject "英语" \
  --year "1984"
```

### 示例 2：处理数学教材照片

```bash
python3 scripts/run_batch.py \
  --output-dir "~/book-output/微积分教程_20260702_01" \
  --book-name "微积分教程" \
  --author "清华编写组" \
  --subject "数学" \
  --year "1975"
```

### 示例 3：从 PDF 电子书提取

```bash
# 1. 准备（扫描+选页+提取）
python3 scripts/prepare_book.py \
  --ebook "~/books/英语语法.pdf" \
  --book-name "英语语法" \
  --pages 3

# 2. 视觉分析（在 Hermes 中手动执行）
# 用 vision_analyze 分析每张内页，保存 JSON 到 analysis/

# 3. 生成
python3 scripts/pipeline.py \
  --skip-vision \
  --output-dir "~/book-output/英语语法_20260702_01" \
  --book-name "英语语法"
```

## 代码结构

```
ai-book-video/
├── SKILL.md                          # Skill 定义
├── README.md                         # 本文档
├── LICENSE                           # MIT License
├── .gitignore
├── assets/
│   └── .env.example                  # 环境变量模板
├── scripts/
│   ├── __init__.py
│   ├── run_batch.py                  # ⭐ 一键运行（推荐）
│   ├── pipeline.py                   # 完整 pipeline
│   ├── prepare_book.py               # 电子书准备
│   ├── ebook_scanner.py              # 电子书页面扫描
│   ├── ebook_extractor.py            # 电子书页面提取
│   ├── page_tracker.py               # 已用页追踪（去重）
│   ├── analyze_page.py               # 视觉分析
│   ├── aging_engine.py               # AI 做旧+标注
│   ├── cover_generator.py            # 封面生成
│   ├── hook_generator.py             # 标题规则引擎
│   ├── output_naming.py              # 输出目录命名
│   ├── description_generator.py      # 图文描述生成
│   ├── description_utils.py          # 描述工具函数
│   ├── quality_checker.py            # 质量校验
│   ├── cleanup.py                    # 生成后清理
│   └── utils.py                      # 工具函数
└── references/                       # 参考文档
    ├── codeproxy-img2img-api.md      # CodeProxy API 文档
    ├── codeproxy-502-pattern.md      # 502 故障处理
    ├── env-key-setup.md              # API Key 配置
    ├── vision-prompt.md              # 视觉分析 prompt
    ├── cover-prompt.md               # 封面生图 prompt
    ├── aging-params.md               # 做旧参数
    ├── ebook-workflow.md             # 电子书流程
    ├── vision-analyze-workflow.md    # vision_analyze 工作流
    ├── hook-patterns.md              # 标题编写模式
    ├── subject-annotations.md        # 学科标注规范
    ├── no-approval-workflow.md       # 无审批工作流
    └── ...
```

## 踩坑记录

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| vision API 返回 404 | 某些 API 不支持图片输入 | 用 Hermes vision_analyze 工具 |
| codeproxy 封面空响应 | 502 故障 | 等 2-5 分钟重试，详见 `references/codeproxy-502-pattern.md` |
| 做旧太暗 | prompt 写了 "vintage" | 改为 "moderate brightness, phone photo" |
| 标注太少 | prompt 只列了 3 种 | 已扩展到 7 类标注 |
| 封面文件找不到 | 用户命名不标准 | 用 `glob('封面*')` 匹配 |
| 同一批图片重复出图 | 没检查已有输出 | 先检查输出目录是否已有 PNG |
| 图文描述为空 | AI API 偶尔返回空 | 自动重试一次 |
| 模板描述学科错误 | 降级时没用 subject | 已修复为 subject 感知 |

## 依赖

### Python 包

```bash
pip install pillow opencv-python requests numpy
```

### Hermes Agent

本 skill 设计为在 [Hermes Agent](https://hermes-agent.nousresearch.com) 中运行，需要以下工具：
- `vision_analyze` — 视觉分析（分析内页内容）
- `write_file` — 保存分析结果
- `terminal` — 运行 Python 脚本
- `image_generate` — 图生图（可选，备选方案）

## License

MIT License - 详见 [LICENSE](LICENSE)

## 致谢

- [CodeProxy](https://codeproxy.dev) — 提供稳定的 gpt-image-2 API
- [Hermes Agent](https://hermes-agent.nousresearch.com) — AI Agent 框架
- [OpenAI](https://openai.com) — gpt-image-2 模型

## 相关链接

- CodeProxy 注册：https://codeproxy.dev/register?aff=TGR5N8MN
- Hermes Agent：https://hermes-agent.nousresearch.com
- 问题反馈：https://github.com/mastercodeai/ai-book-video/issues
