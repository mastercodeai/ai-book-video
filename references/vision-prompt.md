# Vision Analysis Prompt (Stage 1)

Used by `analyze_page.py` with mimo v2.5 to identify key content on each textbook page.

## System Prompt

```
你是一位拥有20年教学经验的学科带头人，极其擅长抓住考试重点。
```

## User Prompt Template

```
请仔细阅读这张教辅书内页图片，完成以下任务：

1. 识别页面上的所有文字内容
2. 找出本页最核心的一句话/公式/知识点（必须与原文一字不差）
3. 判断这段核心文字在图片中的大致位置（以百分比坐标表示，左上角为0,0，右下角为1,1）
4. 针对这句话写一个2-4字的犀利手写批注

请严格按以下JSON格式输出，不要输出其他内容：
{
  "page_topic": "本页主题（10字以内）",
  "key_text": "最核心的原文（一字不差）",
  "bbox": {"x1": 0.1, "y1": 0.3, "x2": 0.9, "y2": 0.35},
  "annotation": "必考！",
  "annotation_position": "right",
  "highlight_lines": [
    {"y": 0.32, "x_start": 0.1, "x_end": 0.9}
  ],
  "secondary_points": [
    {"text": "次要重点1", "bbox": {"x1": 0.1, "y1": 0.5, "x2": 0.9, "y2": 0.55}, "annotation": "注意"}
  ]
}
```

## Output Schema

| Field | Type | Description |
|---|---|---|
| `page_topic` | string | Page topic, ≤10 chars |
| `key_text` | string | The most important text, exact quote from the image |
| `bbox` | object | Bounding box of key_text as percentages (x1,y1 = top-left, x2,y2 = bottom-right) |
| `annotation` | string | 2-4 char handwritten annotation for the key text |
| `annotation_position` | string | Where to place annotation relative to key_text: `"right"`, `"left"`, `"above"`, `"below"` |
| `highlight_lines` | array | List of horizontal highlight bands: `{y, x_start, x_end}` as percentages |
| `secondary_points` | array | Optional additional highlights with their own annotations |

## Parsing Notes

- The model sometimes returns markdown code fences (` ```json ... ``` `) — strip them before parsing.
- Extra text outside the JSON block should be discarded. Extract the first `{...}` block.
- If parsing fails, retry with temperature=0.
- All coordinates are percentages (0.0 to 1.0), NOT pixels. The annotation engine converts them.

## Annotation Style Guide

The annotation text should be:
- **犀利** (sharp/incisive): "必考！", "重点！", "注意", "必背", "核心"
- **Short**: 2-4 characters maximum
- **Exam-oriented**: Focus on what a student would highlight for review
- Avoid generic annotations like "重要" — be specific to the content
