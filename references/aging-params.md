# Aging Parameters (Stage 2)

Pillow-based image aging effects applied by `aging_engine.py`. Effects are applied in order from top to bottom.

## Texture Assets

Location: `D:\Workspace\AI图书带货素材\纹理素材\`

| File | Description | Required |
|---|---|---|
| `yellow_paper.jpg` | Aged yellow paper texture for multiply blend | Yes |
| `tea_stain.jpg` | Tea/coffee stain mark | Yes |
| `crease.jpg` | Paper crease/fold line | Yes |
| `foxing_spots..jpg` | Foxing spots (note: **double dot** in filename) | Yes |

> ⚠️ `foxing_spots..jpg` has a double dot — this is intentional. Do NOT rename.

---

## Effect Parameters

### 1. Desaturation

- **Operation**: Convert to HSV, multiply S channel
- **Factor**: 0.80 (80% of original saturation)
- **Purpose**: Dulls colors to simulate aged paper

```python
hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
hsv[:, :, 1] = (hsv[:, :, 1] * 0.80).astype(np.uint8)
img = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
```

### 2. Warm Brightness Shift

- **Operation**: Multiply brightness channel
- **Factor**: 1.02
- **Purpose**: Adds subtle warm/yellow tint

```python
hsv[:, :, 2] = np.clip(hsv[:, :, 2] * 1.02, 0, 255).astype(np.uint8)
```

### 3. Yellow Texture Overlay

- **Blend mode**: Multiply (PIL `ImageChops.multiply`)
- **Opacity**: 60-80% (randomized per page for variety)
- **Texture**: `yellow_paper.jpg` resized to match image dimensions
- **Purpose**: Primary aging effect — makes paper look yellowed

```python
yellow = Image.open("yellow_paper.jpg").resize(img.size)
opacity = random.uniform(0.60, 0.80)
blended = ImageChops.multiply(img, yellow)
result = Image.blend(img, blended, opacity)
```

### 4. Tea Stain

- **Blend mode**: Overlay (PIL `ImageChops.overlay`)
- **Opacity**: 30-50% (randomized)
- **Position**: Random placement, ensuring at least 60% of stain is within image bounds
- **Scale**: Stain texture scaled to 20-40% of image area
- **Purpose**: Simulates accidental liquid damage

```python
stain = Image.open("tea_stain.jpg")
scale = random.uniform(0.20, 0.40)
stain_size = (int(img.width * scale), int(img.height * scale))
stain = stain.resize(stain_size)
# Random position within bounds
x = random.randint(-stain_size[0] // 4, img.width - 3 * stain_size[0] // 4)
y = random.randint(-stain_size[1] // 4, img.height - 3 * stain_size[1] // 4)
# Paste with opacity
stain_alpha = stain.convert("RGBA")
stain_alpha.putalpha(int(255 * random.uniform(0.30, 0.50)))
img.paste(ImageChops.overlay(img.crop((x, y, x+w, y+h)), stain), (x, y))
```

### 5. Crease

- **Blend mode**: Soft light or overlay
- **Opacity**: 20-40% (randomized)
- **Position**: Random, typically diagonal across the page
- **Rotation**: Random angle 15-75°
- **Purpose**: Simulates folded/worn paper

```python
crease = Image.open("crease.jpg")
angle = random.uniform(15, 75)
crease = crease.rotate(angle, expand=True, fillcolor=(128, 128, 128))
# Scale to 40-80% of image width
scale = random.uniform(0.40, 0.80)
crease = crease.resize((int(img.width * scale), crease.height))
opacity = random.uniform(0.20, 0.40)
```

### 6. Vignette

- **Type**: Radial gradient darkening corners
- **Max darkening**: 30% (multiply by 0.70 at corners)
- **Center**: Brightness preserved (multiply by 1.0)
- **Gradient**: Smooth cosine falloff from center to edges
- **Purpose**: Draws eye to center, simulates uneven lighting

```python
rows, cols = img.shape[:2]
Y, X = np.ogrid[:rows, :cols]
center_y, center_x = rows / 2, cols / 2
dist = np.sqrt((X - center_x)**2 + (Y - center_y)**2)
max_dist = np.sqrt(center_x**2 + center_y**2)
vignette = 1 - 0.30 * (dist / max_dist)  # 0.70 at corners, 1.0 at center
img = (img * vignette[:, :, np.newaxis]).astype(np.uint8)
```

### 7. Edge Wear

- **Type**: Irregular dark border
- **Width**: 5-15px (randomized per edge)
- **Color**: Dark brown/black (RGB ~30, 20, 15)
- **Irregularity**: Each edge gets a different width; noise applied to the boundary
- **Purpose**: Simulates worn, handled edges

```python
edge_widths = {
    'top': random.randint(5, 15),
    'bottom': random.randint(5, 15),
    'left': random.randint(5, 15),
    'right': random.randint(5, 15)
}
# Apply with slight noise for irregularity
mask = create_irregular_edge_mask(img.size, edge_widths)
dark_layer = Image.new('RGB', img.size, (30, 20, 15))
img = Image.composite(dark_layer, img, mask)
```

---

## Effect Order Summary

```
Original Image
  ↓
① Desaturation (80%)
  ↓
② Warm brightness (1.02x)
  ↓
③ Yellow texture (multiply, 60-80%)
  ↓
④ Tea stain (overlay, 30-50%)
  ↓
⑤ Crease (overlay, 20-40%, rotated)
  ↓
⑥ Vignette (30% dark corners)
  ↓
⑦ Edge wear (5-15px irregular border)
  ↓
Aged Image
```

## Randomization

Each page gets slightly different random values within the specified ranges to avoid a uniform "digital" look. The random seed is derived from the page filename for reproducibility.
