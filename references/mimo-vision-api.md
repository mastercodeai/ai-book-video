# Mimo v2.5 Vision API Configuration

## How to Extract API Config from Hermes

When a skill needs to call mimo v2.5 for vision analysis, extract the config from:

```
~/.hermes/config.yaml
```

Look for the `custom_providers` section:

```yaml
custom_providers[0]:
  api_key: tp-cdo1k3rsmazxkx21fes4mcgmrq83dc3rfg3e601ekak3uhcr
  base_url: https://token-plan-cn.xiaomimimo.com/v1
  default: mimo-v2.5-pro
  provider: custom:xiaomi-mimo
```

## API Endpoint

- **Base URL**: `https://token-plan-cn.xiaomimimo.com/v1`
- **Chat completions**: `{base_url}/chat/completions`
- **Model**: `mimo-v2.5-pro`
- **Auth**: Bearer token in Authorization header

## Request Format (OpenAI-compatible)

```json
{
  "model": "mimo-v2.5-pro",
  "messages": [
    {
      "role": "user",
      "content": [
        {"type": "text", "text": "<prompt>"},
        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,<b64>", "detail": "high"}}
      ]
    }
  ],
  "max_tokens": 2000,
  "temperature": 0.3
}
```

## .env Mapping

```
VISION_API_URL=https://token-plan-cn.xiaomimimo.com/v1
VISION_API_KEY=YOUR_VISION_API_KEY_HERE
VISION_MODEL=mimo-v2.5-pro
```

## Pitfalls

- The API key is a long token starting with `tp-`. Do not truncate.
- Temperature 0.3 works well for structured JSON output. Use 0 for retries if JSON parsing fails.
- The `detail: "high"` parameter is important for OCR-quality vision analysis.
- Timeout should be 120s+ for large images.
