"""
Cover image generation via codeproxy.dev gpt-image-2 img2img API.
Transforms a book cover photo into an aged cover with bold hook text.
"""

import os
import re
import time
import json
import base64
from pathlib import Path
from typing import Dict, List, Optional

import requests


def generate_cover_prompt(book_topic: str, page_analyses: List[Dict], config: Dict = None) -> str:
    """
    Generate a prompt for cover image generation (img2img).
    Uses rule-based hook generator for unique, context-aware titles.
    """
    if config is None:
        config = {}

    # Import rule-based hook generator
    from hook_generator import generate_hook_text

    # Extract metadata from config
    author = config.get('author', '')
    year = config.get('year', '')
    subject = config.get('subject', '通用')

    # Extract page topics from analyses
    page_topics = []
    for analysis in page_analyses[:5]:
        if 'page_topic' in analysis:
            page_topics.append(analysis['page_topic'])

    # Generate hook using rule engine
    hook = generate_hook_text(
        book_name=book_topic,
        author=author,
        year=year,
        subject=subject,
        page_topics=page_topics,
    )

    prompt = (
        f"Transform this book cover photo into a worn, heavily used old textbook cover. "
        f"Add realistic aging: yellowed paper, creases, stains, worn edges, "
        f"peeling corners. The book should look like it has been read hundreds of times. "
        f"IMPORTANT: Add a very large, bold red sticker badge across the center of the cover "
        f"with big white Chinese text: \"{hook}\". "
        f"The sticker text must be VERY LARGE and eye-catching, dominating the cover, "
        f"even partially covering the original book title - that's fine. "
        f"The sticker should be slightly tilted like a real sticker. "
        f"A hand should be visible holding the bottom of the book. "
        f"Warm natural lighting as if photographed with a phone. "
        f"The overall brightness should be moderate - not too dark, not too bright, "
        f"like a real phone photo of an old book on a desk."
    )

    print(f"[cover] Hook text: {hook}")
    print(f"[cover] Prompt: {prompt[:100]}...")
    return prompt


def generate_cover_image(
    image_path: str,
    prompt: str,
    output_path: str,
    config: Optional[Dict] = None
) -> str:
    """
    Generate cover image using gpt-image-2 img2img (edits API).

    Args:
        image_path: Path to the original cover photo.
        prompt: Editing prompt describing desired transformations.
        output_path: Path to save the generated image.
        config: Optional config dict with api_base, api_key, model.

    Returns:
        Path to the saved image.
    """
    if config is None:
        config = {}

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image_path = Path(image_path)

    # Get API configuration
    api_base = config.get('api_base') or os.environ.get('IMAGE_API_URL', 'https://codeproxy.dev')
    api_key = config.get('api_key') or os.environ.get('IMAGE_API_KEY', '')
    model = config.get('model', 'gpt-image-2')

    if not api_key:
        raise ValueError("IMAGE_API_KEY not found. Set it in .env or provide in config.")

    url = f"{api_base.rstrip('/')}/v1/images/edits"
    headers = {
        'Authorization': f'Bearer {api_key}'
    }

    max_retries = 3
    last_error = None

    for attempt in range(max_retries):
        try:
            print(f"[cover] Generating cover img2img (attempt {attempt + 1}/{max_retries})...")
            print(f"[cover] URL: {url}")

            with open(image_path, 'rb') as f:
                files = {
                    'image': (image_path.name, f, 'image/jpeg'),
                }
                data = {
                    'model': model,
                    'prompt': prompt,
                    'n': '1',
                }
                resp = requests.post(url, headers=headers, files=files, data=data, timeout=300)

            if resp.status_code != 200:
                error_msg = f"API returned status {resp.status_code}: {resp.text[:200]}"
                print(f"[cover] {error_msg}")
                last_error = Exception(error_msg)
                time.sleep(2 ** attempt)
                continue

            result = resp.json()
            image_item = result.get('data', [{}])[0]

            if 'b64_json' in image_item:
                img_bytes = base64.b64decode(image_item['b64_json'])
                with open(output_path, 'wb') as f:
                    f.write(img_bytes)
                print(f"[cover] Saved cover image: {output_path} ({len(img_bytes)} bytes)")
                return str(output_path)

            elif 'url' in image_item:
                img_resp = requests.get(image_item['url'], timeout=60)
                if img_resp.status_code == 200:
                    with open(output_path, 'wb') as f:
                        f.write(img_resp.content)
                    print(f"[cover] Saved cover image: {output_path}")
                    return str(output_path)
                else:
                    raise Exception(f"Failed to download image: {img_resp.status_code}")
            else:
                raise Exception("No image data in response")

        except Exception as e:
            print(f"[cover] Attempt {attempt + 1} failed: {e}")
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)

    raise Exception(f"Cover generation failed after {max_retries} attempts. Last error: {last_error}")
