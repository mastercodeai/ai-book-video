"""
Utility functions for the ai-book-video skill.
"""

import os
import re
import logging
from pathlib import Path
from typing import Tuple, Optional, Dict, List


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure logging for the skill."""
    logger = logging.getLogger('ai-book-video')
    logger.setLevel(level)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger


def load_env(env_path: Optional[str] = None) -> Dict[str, str]:
    """
    Load environment variables from a .env file.
    
    Args:
        env_path: Path to .env file. If None, looks in assets directory.
    
    Returns:
        Dictionary of environment variables.
    """
    if env_path is None:
        # Look in assets directory relative to this script
        script_dir = Path(__file__).parent.parent
        env_path = script_dir / 'assets' / '.env'
    
    env_path = Path(env_path)
    env_vars = {}
    
    if not env_path.exists():
        print(f"[utils] No .env file found at {env_path}")
        return env_vars
    
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        env_vars[key] = value
                        os.environ[key] = value
        
        print(f"[utils] Loaded {len(env_vars)} environment variables from {env_path}")
    except Exception as e:
        print(f"[utils] Error loading .env file: {e}")
    
    return env_vars


def find_input_images(input_dir: str) -> Dict[str, List[Path]]:
    """
    Find cover and page images in input directory.
    
    Args:
        input_dir: Directory containing book page images.
    
    Returns:
        Dictionary with 'cover' (Path or None) and 'pages' (list of Paths).
    """
    input_path = Path(input_dir)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")
    
    result = {
        'cover': None,
        'pages': []
    }
    
    # Supported image extensions
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
    
    # Find all image files
    all_images = []
    for ext in image_extensions:
        all_images.extend(input_path.glob(f'*{ext}'))
        all_images.extend(input_path.glob(f'*{ext.upper()}'))
    
    # Sort by name
    all_images = sorted(set(all_images), key=lambda p: p.name)
    
    # Separate cover from pages
    cover_pattern = re.compile(r'封面|cover|front', re.IGNORECASE)
    page_pattern = re.compile(r'(\d+)')
    
    for img in all_images:
        if cover_pattern.search(img.stem):
            result['cover'] = img
        else:
            result['pages'].append(img)
    
    # Sort pages by number in filename
    def get_page_number(path: Path) -> int:
        match = page_pattern.search(path.stem)
        return int(match.group(1)) if match else 0
    
    result['pages'].sort(key=get_page_number)
    
    print(f"[utils] Found {1 if result['cover'] else 0} cover + {len(result['pages'])} pages")
    return result


def get_image_dimensions(image_path: str) -> Tuple[int, int]:
    """
    Get image dimensions (width, height).
    
    Args:
        image_path: Path to image file.
    
    Returns:
        Tuple of (width, height).
    """
    from PIL import Image
    
    try:
        with Image.open(image_path) as img:
            return img.size
    except Exception as e:
        print(f"[utils] Error getting dimensions for {image_path}: {e}")
        raise


def percent_to_pixel(bbox: Dict[str, float], width: int, height: int) -> Dict[str, int]:
    """
    Convert percentage-based bounding box to pixel coordinates.
    
    Args:
        bbox: Dictionary with x1, y1, x2, y2 as percentages (0-1).
        width: Image width in pixels.
        height: Image height in pixels.
    
    Returns:
        Dictionary with x1, y1, x2, y2 in pixels.
    """
    return {
        'x1': int(bbox['x1'] * width),
        'y1': int(bbox['y1'] * height),
        'x2': int(bbox['x2'] * width),
        'y2': int(bbox['y2'] * height)
    }


def ensure_dir(path: str) -> Path:
    """
    Create directory if it doesn't exist.
    
    Args:
        path: Directory path to create.
    
    Returns:
        Path object of created directory.
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path
