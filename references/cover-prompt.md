# Cover Generation Prompt (Stage 4)

Used by `cover_generator.py` with gpt-image-2 to generate aged book cover images with bold text overlay.

## Prompt Template

```
A close-up photo of an old, heavily used textbook cover on a wooden desk.
The book looks like it has been read hundreds of times - yellowed pages,
worn edges, coffee stains. Overlaid bold Chinese text: "{hook_text}"
in large eye-catching yellow font with black outline, centered.
Vintage warm lighting, photorealistic, portrait 3:4.
```

## Parameters

| Parameter | Value | Notes |
|---|---|---|
| Aspect ratio | 3:4 (portrait) | Matches typical phone screen for video |
| Style | Photorealistic | Not illustrated or cartoon |
| Lighting | Warm, vintage | Golden/warm tone |
| Text color | Yellow with black outline | High contrast for readability |
| Text position | Centered | On the book cover area |

## Hook Text Generation

The `{hook_text}` should be:
- **Short**: 6-15 characters
- **Attention-grabbing**: Creates curiosity or urgency
- **Book-relevant**: Derived from the book's subject matter

### Examples

| Book Type | Hook Text |
|---|---|
| 高考数学 | "这道题年年考" |
| 英语语法 | "90%的人都搞错了" |
| 物理公式 | "记住这个就够了" |
| 历史考点 | "背下来就是分" |
| 语文作文 | "阅卷老师最爱的开头" |

## API Call

```python
response = client.images.generate(
    model="gpt-image-2",
    prompt=prompt.format(hook_text=hook_text),
    n=1,
    size="1024x1536",  # 3:4 portrait
    quality="high"
)
```

## Backup Model (agnes-image-2.1-flash)

If the primary model fails, use the same prompt with the backup API:

```python
response = requests.post(
    f"{BACKUP_IMAGE_API_URL}/v1/images/generations",
    headers={"Authorization": f"Bearer {BACKUP_IMAGE_API_KEY}"},
    json={
        "model": "agnes-image-2.1-flash",
        "prompt": prompt.format(hook_text=hook_text),
        "n": 1,
        "size": "1024x1536"
    }
)
```

## Post-processing

After generation:
1. Resize to match the source cover dimensions if needed
2. Apply a subtle warm color grade to match the aged page images
3. Save as PNG (no JPEG compression artifacts on text)
