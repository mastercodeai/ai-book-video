# .env API Key 配置指南

## 问题

skill 创建后，.env 中的 API key 可能是占位符（`your_api_key_here`），导致：
- img2img 返回 401
- 描述生成降级到模板模式

## 需要配置的 key

| Key | 来源 | 用途 |
|-----|------|------|
| `IMAGE_API_KEY` | wechat-health-publisher/assets/.env | codeproxy 生图 |
| `VISION_API_KEY` | ~/.hermes/config.yaml → providers.xiaomi-mimo.api_key | mimo 描述生成 |

## 配置方法

### 自动配置（推荐）

在 `~/.hermes/skills/ai-book-video/scripts/` 目录下运行：

```python
import re
from pathlib import Path

# 1. IMAGE_API_KEY：从 wechat-health-publisher 复制
src = Path.home() / 'AppData/Local/hermes/skills/wechat-health-publisher/assets/.env'
src_keys = {}
for line in src.read_text(encoding='utf-8').splitlines():
    line = line.strip()
    if line and not line.startswith('#') and '=' in line:
        k, v = line.split('=', 1)
        src_keys[k.strip()] = v.strip()

# 2. VISION_API_KEY：从 Hermes config 读取
config = Path.home() / 'AppData/Local/hermes/config.yaml'
mimo_key = ''
for line in config.read_text().splitlines():
    line = line.strip()
    if line.startswith('tp-') and len(line) > 20:
        mimo_key = line
        break

# 3. 写入 .env
env_path = Path.home() / 'AppData/Local/hermes/skills/ai-book-video/assets/.env'
content = env_path.read_text(encoding='utf-8')
for key in ['IMAGE_API_KEY', 'IMAGE_API_URL']:
    val = src_keys.get(key, '')
    if val:
        content = re.sub(f'^{key}=.*', f'{key}={val}', content, flags=re.MULTILINE)
if mimo_key:
    content = re.sub(r'^VISION_API_KEY=YOUR_VISION_API_KEY_HERE f'VISION_API_KEY=YOUR_VISION_API_KEY_HERE content, flags=re.MULTILINE)
env_path.write_text(content, encoding='utf-8')
print('Done')
```

### 手动配置

直接编辑 `~/.hermes/skills/ai-book-video/assets/.env`：

```
IMAGE_API_URL=https://codeproxy.dev
IMAGE_API_KEY=YOUR_IMAGE_API_KEY_HERE
VISION_API_URL=https://token-plan-cn.xiaomimimo.com/v1
VISION_API_KEY=YOUR_VISION_API_KEY_HERE
VISION_MODEL=mimo-v2.5-pro
```

## 验证

```bash
# 检查 key 是否为真实值（不是占位符）
grep -E "^(IMAGE|VISION)_API_KEY=" ~/.hermes/skills/ai-book-video/assets/.env
# 应该看到真实的 key 值，不是 "your_..." 开头
```

## 何时需要重新配置

- skill 更新/重建时（subagent 可能用占位符覆盖 .env）
- 出现 API 401 错误时
- 描述生成持续降级到模板模式时
- wechat-health-publisher 的 key 更新后
