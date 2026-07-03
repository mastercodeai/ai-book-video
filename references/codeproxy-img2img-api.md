# Codeproxy 图生图 API (img2img)

## 端点

```
POST https://codeproxy.dev/v1/images/edits
```

## 参数

| 参数 | 类型 | 说明 |
|------|------|------|
| model | string | `"gpt-image-2"` |
| prompt | string | 编辑指令（英文效果更好） |
| n | string | `"1"`（注意是字符串不是数字） |
| image | file | 原始图片文件（multipart/form-data） |

## Python 调用

```python
import requests

url = "https://codeproxy.dev/v1/images/edits"
headers = {"Authorization": "Bearer YOUR_API_KEY"}

with open("input.jpg", "rb") as f:
    files = {"image": ("input.jpg", f, "image/jpeg")}
    data = {"model": "gpt-image-2", "prompt": "your prompt here", "n": "1"}
    resp = requests.post(url, headers=headers, files=files, data=data, timeout=300)

result = resp.json()
# result["data"][0]["b64_json"] — base64 图片
```

## 响应格式

```json
{
  "created": 1234567890,
  "data": [{"b64_json": "iVBORw0KGgo..."}]
}
```

## 踩坑

- **必须走代理**：直连 codeproxy.dev 会超时，需设置 `HTTPS_PROXY=http://127.0.0.1:7897`
- **n 是字符串**：传 `"1"` 不是 `1`
- **timeout 要大**：单张图约 60-120 秒，设 300 秒
- **quality 参数不支持**：不要传 quality 字段，会返回空响应
- **不要用 BACKUP_APIS 逻辑**：多 API fallback 会导致请求混乱，用单 API + 重试即可
