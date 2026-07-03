"""
Vision analysis module for book page images.
Uses OpenAI-compatible API to analyze book page content.
"""

import os
import re
import json
import base64
import time
from pathlib import Path
from typing import Dict, Optional


VISION_PROMPT = """你是一位拥有20年教学经验的学科带头人，极其擅长抓住考试重点。

请仔细阅读这张教辅书内页图片，完成以下任务：

1. 识别页面上的所有文字内容
2. 找出本页最核心的一句话/公式/知识点（必须与原文一字不差）
3. 判断这段核心文字在图片中的大致位置（以百分比坐标表示，左上角为0,0，右下角为1,1）
4. 针对这句话写一个2-4字的犀利手写批注

请严格按以下JSON格式输出，不要输出其他内容：
{
  "page_topic": "本页主题（10字以内）",
  "key_text": "最核心的原文（一字不差）",
  "bbox": {"x1": 0.1, "y1": 0.3, "x2": 0.9, "y2": 0.35},
  "annotation": "必考！",
  "annotation_position": "right",
  "highlight_lines": [{"y": 0.32, "x_start": 0.1, "x_end": 0.9}],
  "secondary_points": [{"text": "次要重点1", "bbox": {"x1": 0.1, "y1": 0.5, "x2": 0.9, "y2": 0.55}, "annotation": "注意"}]
}"""


def encode_image_to_base64(image_path: str) -> str:
    """
    Encode an image file to base64 string.
    
    Args:
        image_path: Path to the image file.
    
    Returns:
        Base64 encoded string of the image.
    """
    with open(image_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')


def extract_json_from_text(text: str) -> Optional[Dict]:
    """
    Extract JSON from text that might contain other content.
    
    Args:
        text: Text that should contain JSON.
    
    Returns:
        Parsed JSON dict or None if extraction fails.
    """
    # Try direct JSON parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Try to find JSON block in markdown code fence
    json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
    
    # Try to find JSON object with regex (greedy match for outermost braces)
    json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass
    
    # Try a more permissive approach - find first { and last }
    first_brace = text.find('{')
    last_brace = text.rfind('}')
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        try:
            return json.loads(text[first_brace:last_brace + 1])
        except json.JSONDecodeError:
            pass
    
    return None


def validate_analysis_data(data: Dict) -> bool:
    """
    Validate that analysis data has required fields.
    
    Args:
        data: Analysis data dictionary.
    
    Returns:
        True if valid, False otherwise.
    """
    required_fields = ['page_topic', 'key_text', 'bbox', 'annotation']
    
    for field in required_fields:
        if field not in data:
            return False
    
    # Validate bbox structure
    bbox = data.get('bbox', {})
    if not all(k in bbox for k in ['x1', 'y1', 'x2', 'y2']):
        return False
    
    # Validate bbox values are in range
    for key in ['x1', 'y1', 'x2', 'y2']:
        val = bbox.get(key, -1)
        if not (0 <= val <= 1):
            return False
    
    return True


def analyze_page(image_path: str, config: Optional[Dict] = None) -> Dict:
    """
    Analyze a book page image using vision API.
    
    Args:
        image_path: Path to the page image.
        config: Configuration dict with API settings:
            - api_base: API base URL (default: from OPENAI_API_BASE env)
            - api_key: API key (default: from OPENAI_API_KEY env)
            - model: Model name (default: 'mimo-v2.5')
    
    Returns:
        Analysis dict with page_topic, key_text, bbox, annotation, etc.
    
    Raises:
        Exception: If analysis fails after all retries.
    """
    if config is None:
        config = {}
    
    # Get API configuration (check VISION_* vars first, then OPENAI_* fallback)
    api_base = config.get('api_base') or os.environ.get('VISION_API_URL') or os.environ.get('OPENAI_API_BASE', 'https://api.openai.com/v1')
    api_key = config.get('api_key') or os.environ.get('VISION_API_KEY') or os.environ.get('OPENAI_API_KEY', '')
    model = config.get('model', os.environ.get('VISION_MODEL', 'mimo-v2.5-pro'))
    
    if not api_key:
        raise ValueError("API key not found. Set OPENAI_API_KEY or provide in config.")
    
    # Remove trailing slash from API base
    api_base = api_base.rstrip('/')
    
    # Encode image
    print(f"[analyze_page] Encoding image: {image_path}")
    image_base64 = encode_image_to_base64(image_path)
    
    # Determine MIME type
    ext = Path(image_path).suffix.lower()
    mime_map = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
                '.bmp': 'image/bmp', '.webp': 'image/webp'}
    mime_type = mime_map.get(ext, 'image/jpeg')
    
    # Prepare request payload
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": VISION_PROMPT
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{image_base64}",
                            "detail": "high"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 2000,
        "temperature": 0.3
    }
    
    # Retry logic
    max_retries = 3
    last_error = None
    
    for attempt in range(max_retries):
        try:
            print(f"[analyze_page] Sending request (attempt {attempt + 1}/{max_retries})...")
            
            # Use requests library
            import requests
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}'
            }
            
            url = f"{api_base}/chat/completions"
            response = requests.post(url, json=payload, headers=headers, timeout=120)
            
            if response.status_code != 200:
                error_msg = f"API returned status {response.status_code}: {response.text}"
                print(f"[analyze_page] {error_msg}")
                last_error = Exception(error_msg)
                time.sleep(2 ** attempt)
                continue
            
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            print(f"[analyze_page] Got response, parsing JSON...")
            
            # Parse JSON from response
            analysis = extract_json_from_text(content)
            
            if analysis is None:
                error_msg = f"Could not extract JSON from response: {content[:200]}..."
                print(f"[analyze_page] {error_msg}")
                last_error = Exception(error_msg)
                time.sleep(2 ** attempt)
                continue
            
            # Validate response
            if not validate_analysis_data(analysis):
                error_msg = f"Invalid analysis data structure: {analysis}"
                print(f"[analyze_page] {error_msg}")
                last_error = Exception(error_msg)
                time.sleep(2 ** attempt)
                continue
            
            # Add defaults for optional fields
            analysis.setdefault('annotation_position', 'right')
            analysis.setdefault('highlight_lines', [])
            analysis.setdefault('secondary_points', [])
            
            print(f"[analyze_page] Successfully analyzed: {analysis.get('page_topic', 'Unknown')}")
            return analysis
            
        except Exception as e:
            print(f"[analyze_page] Attempt {attempt + 1} failed: {e}")
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
    
    raise Exception(f"Analysis failed after {max_retries} attempts. Last error: {last_error}")


def analyze_page_cached(cache_path: str) -> Dict:
    """
    Load cached analysis results from JSON file.
    
    Args:
        cache_path: Path to cached JSON file.
    
    Returns:
        Analysis dict loaded from cache.
    """
    cache_path = Path(cache_path)
    
    if not cache_path.exists():
        raise FileNotFoundError(f"Cache file not found: {cache_path}")
    
    with open(cache_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"[analyze_page] Loaded cached analysis from {cache_path}")
    return data
