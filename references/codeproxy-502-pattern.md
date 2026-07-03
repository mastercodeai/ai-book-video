# codeproxy 502 故障模式与重试策略

## 现象

codeproxy.dev 的 `/v1/images/edits` 和 `/v1/images/generations` 端点偶尔返回 502：
```json
{"error":{"message":"Upstream service temporarily unavailable","type":"upstream_error"}}
```

## 原因

codeproxy 是代理服务，上游是 OpenAI。502 表示 OpenAI 侧临时不可用。

## 触发条件

- 长时间连续调用（批量生图 5+ 张后）
- OpenAI 自身维护/过载
- 代理端口 7897 连接池耗尽

## 重试策略

| 持续时间 | 动作 |
|----------|------|
| 首次 502 | 立即重试（run_batch.py 已内置 3 次重试） |
| 持续 2-5 分钟 | 等 30 秒后重试 |
| 持续 5-10 分钟 | 等 2 分钟后重试 |
| 持续 10+ 分钟 | 停止，等 15-30 分钟后再跑 |

## 诊断命令

```bash
# 测试 codeproxy 可达性
curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 -x http://127.0.0.1:7897 https://codeproxy.dev

# 测试文生图端点
curl -s -X POST -x http://127.0.0.1:7897 \
  https://codeproxy.dev/v1/images/generations \
  -H "Authorization: Bearer $IMAGE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-image-2","prompt":"test","n":1,"size":"1024x1024"}' \
  -w "\nStatus: %{http_code}" --max-time 30

# 200=正常, 502=上游故障, 401=key问题, 超时=代理问题
```

## 验证过的恢复记录

- 2026-06-29: 502 持续约 5 分钟后自动恢复
- 2026-07-02: 502 持续约 3 分钟后恢复，重试成功
