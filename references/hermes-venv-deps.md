# Hermes venv Dependency Installation

## Problem

The Hermes desktop app runs Python from its own virtualenv:
`C:\Users\Administrator\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe`

Running `pip install <package>` installs into the system Python (`C:\Program Files\Python311\Lib\site-packages`), which the Hermes venv cannot see.

## Solution

Use `uv pip install` with explicit `--python` targeting the Hermes venv:

```bash
uv pip install pillow opencv-python requests numpy \
  --python "$HOME/AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe"
```

## Verification

```bash
python3 -c "import PIL; import cv2; import numpy; import requests; print('All deps OK')"
```

## Packages Needed for ai-book-video

| Package | Purpose |
|---------|---------|
| pillow | Image processing (aging, annotation) |
| opencv-python | Wavy line drawing |
| numpy | Array operations for blend modes |
| requests | API calls (vision, cover generation) |
