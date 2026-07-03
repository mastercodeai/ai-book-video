"""
Aging + annotation engine using AI img2img (codeproxy /v1/images/edits).
Transforms clean book page photos into aged pages with handwritten annotations.
"""

import os
import time
import base64
from pathlib import Path
from typing import Dict, Optional

import requests


def generate_page_prompt(analysis_data: Dict, subject: str = '英语') -> str:
    """
    Generate an img2img prompt for transforming a clean book page into
    an aged page with handwritten annotations.

    Args:
        analysis_data: Vision analysis dict with key_text, annotation, etc.
        subject: Book subject (英语/数学/语文/通用) for annotation labels.

    Returns:
        Prompt string for the img2img API.
    """
    annotation = analysis_data.get('annotation', '必考！')
    key_text = analysis_data.get('key_text', '')[:30]
    page_topic = analysis_data.get('page_topic', '')

    # Subject-specific annotation labels
    subject_labels = {
        '英语': 'grammar labels like 主语, 谓语, 宾语, 状语, 表语, 定语',
        '数学': 'math labels like 公式, 定理, 解题关键, 易错, 步骤1, 步骤2',
        '语文': 'Chinese labels like 修辞手法, 中心思想, 关键词, 段落大意, 写作手法',
        '文言': 'classical Chinese labels like 实词, 虚词, 古今异义, 词类活用, 特殊句式',
        '物理': 'physics labels like 公式, 原理, 受力分析, 解题关键, 易错点',
        '化学': 'chemistry labels like 反应方程式, 实验步骤, 注意安全, 易错',
        '通用': 'study labels like 重点, 难点, 考点, 易错, 必背, 理解',
    }
    labels = subject_labels.get(subject, subject_labels['通用'])

    # Secondary annotations
    secondary_parts = []
    for sp in analysis_data.get('secondary_points', []):
        ann = sp.get('annotation', '')
        text = sp.get('text', '')[:20]
        if ann:
            secondary_parts.append(ann)
        if text:
            secondary_parts.append(text)

    secondary_text = ''
    if secondary_parts:
        secondary_text = (
            f' Also add these blue handwritten annotations around the page: '
            f'{", ".join(secondary_parts[:4])}. '
            f'Write them in blue ballpoint pen next to relevant sentences.'
        )

    prompt = (
        f"Transform this textbook page photo into a heavily used old book page "
        f"that looks like a real student has been studying it intensively. "
        f"Add realistic aging: slightly yellowed paper (not too dark, moderate brightness), "
        f"light foxing spots, subtle coffee stains, creased corners, worn edges. "
        f"The lighting should look natural, like a phone photo taken on a desk. "
        f"IMPORTANT - Add many handwritten study annotations to show intensive studying: "
        f"1. A red wavy underline under the most important sentence. "
        f"2. A bold red handwritten annotation \"{annotation}\" next to the key text. "
        f"3. Blue box brackets [ ] around the section title. "
        f"4. Red circles around key terms. "
        f"5. Small handwritten notes in the margins with {labels}. "
        f"6. Yellow highlight marks on important phrases. "
        f"7. Small stars or checkmarks next to key points. "
        f"{secondary_text} "
        f"The annotations should look messy but authentic - like a real student's "
        f"study notes made with red and blue ballpoint pens over many study sessions. "
        f"Keep all original printed text clearly readable. "
        f"The overall image should be bright enough to read easily, "
        f"like a phone photo of a book page under room lighting."
    )

    return prompt


def apply_aging_and_annotations(
    image_path: str,
    analysis_data: Dict,
    output_path: str,
    config: Optional[Dict] = None,
    subject: str = '英语'
) -> str:
    """
    Apply aging effects and handwritten annotations to a book page image
    using AI img2img.

    Args:
        image_path: Path to the original clean page photo.
        analysis_data: Vision analysis dict from analyze_page.
        output_path: Path to save the processed image.
        config: Optional config dict with api_base, api_key, model.
        subject: Book subject for annotation labels (英语/数学/语文/文言/物理/化学/通用).

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

    # Generate prompt from analysis data
    prompt = generate_page_prompt(analysis_data, subject)
    print(f"[page] Prompt: {prompt[:120]}...")

    url = f"{api_base.rstrip('/')}/v1/images/edits"
    headers = {
        'Authorization': f'Bearer {api_key}'
    }

    max_retries = 3
    last_error = None

    for attempt in range(max_retries):
        try:
            print(f"[page] Processing img2img (attempt {attempt + 1}/{max_retries})...")

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
                print(f"[page] {error_msg}")
                last_error = Exception(error_msg)
                time.sleep(2 ** attempt)
                continue

            result = resp.json()
            image_item = result.get('data', [{}])[0]

            if 'b64_json' in image_item:
                img_bytes = base64.b64decode(image_item['b64_json'])
                with open(output_path, 'wb') as f:
                    f.write(img_bytes)
                print(f"[page] Saved: {output_path} ({len(img_bytes)} bytes)")
                return str(output_path)

            elif 'url' in image_item:
                img_resp = requests.get(image_item['url'], timeout=60)
                if img_resp.status_code == 200:
                    with open(output_path, 'wb') as f:
                        f.write(img_resp.content)
                    print(f"[page] Saved: {output_path}")
                    return str(output_path)
                else:
                    raise Exception(f"Download failed: {img_resp.status_code}")
            else:
                raise Exception("No image data in response")

        except Exception as e:
            print(f"[page] Attempt {attempt + 1} failed: {e}")
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)

    raise Exception(f"Page processing failed after {max_retries} attempts. Last error: {last_error}")
