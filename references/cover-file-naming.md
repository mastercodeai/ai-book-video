# 封面文件命名约定

用户的封面文件命名不固定，需要在运行时搜索匹配。

## 已知命名模式

| 模式 | 示例 | 频率 |
|------|------|------|
| `封面.jpg` | 封面.jpg | 最常见 |
| `封面-书名.jpg` | 封面-微积分.jpg | 常见 |
| `封面_书名.jpg` | 封面_英语.jpg | 偶尔 |
| `cover.jpg` | cover.jpg | 罕见 |

## 匹配方法

```python
# 在 pipeline 中搜索封面文件
import glob
import os

input_dir = r'D:\Workspace\AI图书带货素材\原始图片'
cover_patterns = ['封面*', 'cover*']
cover_file = None

for pattern in cover_patterns:
    matches = glob.glob(os.path.join(input_dir, pattern))
    if matches:
        cover_file = matches[0]
        break

if not cover_file:
    print("Warning: No cover file found")
```

## 注意事项

- 封面文件扩展名可能是 .jpg、.jpeg、.png
- 搜索时忽略大小写
- 如果找到多个匹配，取第一个
- 封面文件在 pipeline 中用于生成封面大字图（img2img）
