# vision_analyze 工作流

## 为什么不能用 API 直接调用

mimo v2.5 API (`https://token-plan-cn.xiaomimimo.com/v1`) 不支持图片输入。
直接发送含 `image_url` 的 chat completions 请求会返回：
```json
{"error":{"code":"404","message":"No endpoints found that support image input"}}
```

## 正确的工作流

### Step 1: 对每张内页调用 vision_analyze

在 Hermes 对话中，对每张内页图片调用 `vision_analyze` 工具：

```
vision_analyze(
  image_url="D:\\Workspace\\AI图书带货素材\\原始图片\\1.jpg",
  question="你是一位拥有20年教学经验的学科带头人...（完整prompt见 vision-prompt.md）"
)
```

### Step 2: 保存 JSON 结果

将 vision_analyze 返回的 `analysis` 字段（JSON 字符串）解析并保存：

```python
import json
from pathlib import Path

analysis_data = json.loads(vision_analyze_result['analysis'])
output_dir = Path("D:/Workspace/AI图书带货素材/教辅书_时间戳/analysis")
output_dir.mkdir(parents=True, exist_ok=True)

(output_dir / "1.json").write_text(
    json.dumps(analysis_data, ensure_ascii=False, indent=2),
    encoding='utf-8'
)
```

### Step 3: 跑 pipeline

```bash
python scripts/pipeline.py --book-name "书名" --skip-vision
```

## JSON 格式要求

vision_analyze 返回的 JSON 必须包含以下字段：

```json
{
  "page_topic": "本页主题（10字以内）",
  "key_text": "最核心的原文（一字不差）",
  "bbox": {"x1": 0.1, "y1": 0.3, "x2": 0.9, "y2": 0.35},
  "annotation": "必考！",
  "annotation_position": "right",
  "highlight_lines": [{"y": 0.32, "x_start": 0.1, "x_end": 0.9}],
  "secondary_points": [
    {"text": "次要重点1", "bbox": {"x1": 0.1, "y1": 0.5, "x2": 0.9, "y2": 0.55}, "annotation": "注意"}
  ]
}
```

## 批量处理技巧

当内页较多时（>5张），可以并行调用 vision_analyze：

```python
# 在 Hermes 中同时调用多个 vision_analyze（并行执行）
vision_analyze(image_url="...1.jpg", question="...")
vision_analyze(image_url="...2.jpg", question="...")
vision_analyze(image_url="...3.jpg", question="...")
```

然后一次性保存所有 JSON 文件。

## 踩坑记录

- vision_analyze 返回的 JSON 可能包含 markdown code fence（```json...```），需要用正则提取
- bbox 坐标是百分比（0-1），不是像素坐标
- annotation 字段限制 2-4 个字，超过会导致标注渲染位置偏移
- 教辅书内容识别准确率高，但纯图片/图表页面可能返回空结果
