"""
Annotation rendering engine using Pillow.
Draws handwritten annotations, underlines, and highlights on book page images.
"""

import math
import random
from pathlib import Path
from typing import Dict, List, Optional

from PIL import Image, ImageDraw, ImageFont
import numpy as np


def render_annotations(
    image_path: str,
    analysis_data: Dict,
    font_path: str,
    output_path: str
) -> str:
    """
    Render annotations on an aged book page image.
    
    Args:
        image_path: Path to the aged image.
        analysis_data: Analysis dict from analyze_page containing:
            - bbox: {x1, y1, x2, y2} as percentages
            - annotation: Text to write
            - annotation_position: 'right' or 'left'
            - highlight_lines: List of {y, x_start, x_end}
            - secondary_points: List of {text, bbox, annotation}
        font_path: Path to font file (e.g., simkai.ttf).
        output_path: Path to save the annotated image.
    
    Returns:
        Path to the output image.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"[annotation] Loading image: {image_path}")
    img = Image.open(image_path).convert('RGBA')
    width, height = img.size
    
    # Create drawing overlay
    overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Load font
    font_size = random.randint(26, 30)
    try:
        font = ImageFont.truetype(font_path, font_size)
        print(f"[annotation] Loaded font: {font_path} (size: {font_size})")
    except Exception as e:
        print(f"[annotation] Warning: Could not load font {font_path}: {e}")
        font = ImageFont.load_default()
    
    # Draw main annotation
    bbox_data = analysis_data.get('bbox', {})
    annotation_text = analysis_data.get('annotation', '')
    annotation_position = analysis_data.get('annotation_position', 'right')
    
    if bbox_data and annotation_text:
        # Convert percentage bbox to pixel coordinates
        px_bbox = {
            'x1': int(bbox_data['x1'] * width),
            'y1': int(bbox_data['y1'] * height),
            'x2': int(bbox_data['x2'] * width),
            'y2': int(bbox_data['y2'] * height)
        }
        
        # Draw wavy underline
        print("[annotation] Drawing wavy underline...")
        _draw_wavy_underline(draw, px_bbox, width, height)
        
        # Draw highlight rectangle (semi-transparent yellow)
        print("[annotation] Drawing highlight...")
        _draw_highlight(draw, px_bbox)
        
        # Draw annotation text
        print(f"[annotation] Drawing annotation: {annotation_text}")
        _draw_annotation_text(draw, annotation_text, px_bbox, font, annotation_position, width, height)
    
    # Draw highlight lines
    highlight_lines = analysis_data.get('highlight_lines', [])
    for line in highlight_lines:
        _draw_highlight_line(draw, line, width, height)
    
    # Draw secondary points
    secondary_points = analysis_data.get('secondary_points', [])
    if secondary_points:
        print(f"[annotation] Drawing {len(secondary_points)} secondary points...")
        try:
            secondary_font = ImageFont.truetype(font_path, font_size - 4)
        except Exception:
            secondary_font = font
        
        for point in secondary_points:
            if 'bbox' in point and 'annotation' in point:
                sec_bbox = {
                    'x1': int(point['bbox']['x1'] * width),
                    'y1': int(point['bbox']['y1'] * height),
                    'x2': int(point['bbox']['x2'] * width),
                    'y2': int(point['bbox']['y2'] * height)
                }
                
                # Draw secondary underline
                _draw_wavy_underline(draw, sec_bbox, width, height, is_secondary=True)
                
                # Draw secondary annotation
                _draw_annotation_text(
                    draw, point['annotation'], sec_bbox, secondary_font,
                    'right', width, height, is_secondary=True
                )
    
    # Composite overlay onto image
    result = Image.alpha_composite(img, overlay)
    
    # Convert to RGB for saving as JPEG
    if output_path.suffix.lower() in ['.jpg', '.jpeg']:
        result = result.convert('RGB')
    
    result.save(str(output_path), quality=95)
    print(f"[annotation] Saved annotated image: {output_path}")
    
    return str(output_path)


def _draw_wavy_underline(
    draw: ImageDraw.Draw,
    bbox: Dict[str, int],
    img_width: int,
    img_height: int,
    is_secondary: bool = False
):
    """Draw a wavy underline under the bbox using sine wave + noise."""
    # Underline parameters
    color = (180, 30, 30, 200) if not is_secondary else (180, 30, 30, 150)
    line_width = random.randint(2, 4)
    amplitude = random.uniform(2, 3)
    frequency = random.uniform(0.05, 0.1)
    
    # Underline position (slightly below bbox)
    y_base = bbox['y2'] + 5
    x_start = bbox['x1']
    x_end = bbox['x2']
    
    # Generate wavy line points
    points = []
    for x in range(x_start, x_end, 2):
        # Sine wave + random noise
        y_offset = amplitude * math.sin(frequency * x) + random.uniform(-0.5, 0.5)
        y = int(y_base + y_offset)
        points.append((x, y))
    
    # Draw the wavy line
    if len(points) >= 2:
        for i in range(len(points) - 1):
            draw.line([points[i], points[i + 1]], fill=color, width=line_width)


def _draw_highlight(draw: ImageDraw.Draw, bbox: Dict[str, int]):
    """Draw semi-transparent yellow highlight rectangle."""
    # Yellow highlight with low opacity
    highlight_color = (255, 255, 100, 40)
    
    # Draw filled rectangle
    draw.rectangle(
        [bbox['x1'], bbox['y1'], bbox['x2'], bbox['y2']],
        fill=highlight_color,
        outline=None
    )


def _draw_annotation_text(
    draw: ImageDraw.Draw,
    text: str,
    bbox: Dict[str, int],
    font: ImageFont.FreeTypeFont,
    position: str,
    img_width: int,
    img_height: int,
    is_secondary: bool = False
):
    """Draw handwritten annotation text with rotation."""
    # Choose color: random dark red or dark blue
    if random.random() < 0.6:
        color = (160, 30, 30, 220)  # Dark red
    else:
        color = (30, 40, 120, 220)  # Dark blue
    
    if is_secondary:
        color = (color[0], color[1], color[2], 160)
    
    # Get text size
    try:
        text_bbox = font.getbbox(text)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
    except AttributeError:
        # Fallback for older Pillow versions
        text_width, text_height = draw.textsize(text, font=font)
    
    # Position text
    if position == 'right':
        x = bbox['x2'] + 15
        y = bbox['y1'] - 5
    else:  # left
        x = bbox['x1'] - text_width - 15
        y = bbox['y1'] - 5
    
    # Ensure text stays within image bounds
    x = max(10, min(x, img_width - text_width - 10))
    y = max(10, min(y, img_height - text_height - 10))
    
    # Apply random rotation (-5° to +5°)
    rotation = random.uniform(-5, 5)
    
    # Create temporary image for rotated text
    text_img = Image.new('RGBA', (text_width + 20, text_height + 20), (0, 0, 0, 0))
    text_draw = ImageDraw.Draw(text_img)
    text_draw.text((10, 10), text, font=font, fill=color)
    
    # Rotate text
    text_img = text_img.rotate(rotation, expand=True, resample=Image.BICUBIC)
    
    # Paste onto main overlay
    # We need to access the parent image, but we only have draw
    # Store the text image for later compositing
    draw._image.paste(text_img, (x - 10, y - 10), text_img)


def _draw_highlight_line(
    draw: ImageDraw.Draw,
    line_data: Dict,
    img_width: int,
    img_height: int
):
    """Draw a highlight line from analysis data."""
    y = int(line_data.get('y', 0) * img_height)
    x_start = int(line_data.get('x_start', 0) * img_width)
    x_end = int(line_data.get('x_end', 1) * img_width)
    
    # Draw a semi-transparent line
    color = (255, 255, 100, 50)
    line_width = max(3, int(img_height * 0.005))
    
    draw.line([(x_start, y), (x_end, y)], fill=color, width=line_width)
