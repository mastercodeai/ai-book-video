# 图文描述模板降级修复

## 问题
description_generator.py 的模板降级模式中，`SELLING_POINT_TEMPLATES` 硬编码了"学英语"：
```python
"不讲空话，不堆词表，把中国人学英语的核心规律，编成口诀，好懂又好记"
```

当处理数学/语文/文言等非英语书籍时，降级描述会错误地写"学英语"。

## 修复方案
将模板中的"学英语"替换为 `{subject}` 变量，在 `generate_description()` 函数中根据 config.subject 动态替换。

模板中需要变量替换的字段：
- "学英语" → "学{subject}"
- "英语的核心规律" → "{subject}的核心规律"

## 修复位置
`scripts/description_generator.py` → `generate_description()` 函数中的 `SELLING_POINT_TEMPLATES` 列表

## 验证
修复后，用 `subject='数学'` 测试模板降级，确认输出不含"学英语"。
