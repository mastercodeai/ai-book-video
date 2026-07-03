"""
Ebook page scanner — identifies page types (cover, TOC, preface, content, exercise)
by analyzing extracted page images. Uses text density and layout heuristics.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

try:
    import pymupdf
except ImportError:
    pymupdf = None


def scan_ebook_pages(
    ebook_path: str,
    output_dir: str,
    scan_range: int = 15,
    dpi: int = 200,
) -> Dict:
    """
    Extract and scan the first N pages of an ebook to identify page types.

    Returns:
        Dict with:
        - total_pages: int
        - scanned_pages: list of dicts with {page_num, image_path, text_density, has_text}
        - content_start_hint: estimated first content page (1-indexed)
    """
    if pymupdf is None:
        raise ImportError("pymupdf not installed")

    ebook_path = Path(ebook_path)
    output_dir = Path(output_dir)
    scan_dir = output_dir / '_scan'
    scan_dir.mkdir(parents=True, exist_ok=True)

    doc = pymupdf.open(str(ebook_path))
    total = len(doc)
    zoom = dpi / 72.0
    mat = pymupdf.Matrix(zoom, zoom)

    scanned = []
    total_text_len = 0
    print(f"[scan] Scanning first {min(scan_range, total)} of {total} pages...")

    for i in range(min(scan_range, total)):
        page = doc[i]
        text = page.get_text().strip()
        text_len = len(text)
        char_count = len([c for c in text if '\u4e00' <= c <= '\u9fff' or c.isalpha()])
        total_text_len += text_len

        # Save page image
        pix = page.get_pixmap(matrix=mat)
        img_path = scan_dir / f'page_{i+1:02d}.png'
        pix.save(str(img_path))

        # Analyze image content (for scanned PDFs where text extraction fails)
        img_data = pix.samples
        img_w, img_h = pix.width, pix.height
        # Count non-white pixels as a proxy for content density
        non_white = sum(1 for b in img_data if b < 240)
        total_pixels = img_w * img_h
        content_ratio = non_white / total_pixels if total_pixels > 0 else 0

        page_info = {
            'page_num': i + 1,
            'image_path': str(img_path),
            'text_length': text_len,
            'char_count': char_count,
            'has_text': text_len > 20,
            'content_ratio': round(content_ratio, 3),
            'is_likely_content': False,
        }
        scanned.append(page_info)

        # Heuristic for content detection:
        # - Text-based PDF: use char_count > 100
        # - Scanned PDF: use content_ratio (pages with lots of text have ratio 0.05-0.15)
        if char_count > 100:
            page_info['is_likely_content'] = True
        elif text_len == 0 and content_ratio > 0.03:
            # Scanned page with substantial content (not blank, not just cover image)
            page_info['is_likely_content'] = True

        status = f"text={text_len} chars={char_count} density={content_ratio:.3f}"
        if page_info['is_likely_content']:
            status += " [LIKELY CONTENT]"
        elif text_len > 0:
            status += " [FRONT MATTER]"
        else:
            status += " [IMAGE/BLANK]"

        print(f"  Page {i+1}: {status}")

    doc.close()

    # Estimate content start: first page with substantial text
    content_start = None
    for p in scanned:
        if p['is_likely_content']:
            content_start = p['page_num']
            break

    result = {
        'ebook_path': str(ebook_path),
        'total_pages': total,
        'scanned_pages': scanned,
        'content_start_page': content_start,
        'scan_dir': str(scan_dir),
    }

    # Save scan result
    scan_result_path = output_dir / 'scan_result.json'
    with open(scan_result_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n[scan] Content likely starts at page {content_start}")
    print(f"[scan] Result saved: {scan_result_path}")

    return result


def extract_content_pages(
    ebook_path: str,
    output_dir: str,
    page_numbers: List[int],
    dpi: int = 200,
) -> List[Path]:
    """
    Extract specific pages from ebook as images.

    Args:
        ebook_path: Path to the ebook.
        output_dir: Directory to save extracted pages.
        page_numbers: List of 1-indexed page numbers to extract.
        dpi: Rendering resolution.

    Returns:
        List of paths to extracted page images.
    """
    if pymupdf is None:
        raise ImportError("pymupdf not installed")

    ebook_path = Path(ebook_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    doc = pymupdf.open(str(ebook_path))
    zoom = dpi / 72.0
    mat = pymupdf.Matrix(zoom, zoom)

    extracted = []
    for page_num in page_numbers:
        idx = page_num - 1  # Convert to 0-indexed
        if 0 <= idx < len(doc):
            page = doc[idx]
            pix = page.get_pixmap(matrix=mat)
            out_path = output_dir / f'{page_num}.png'
            pix.save(str(out_path))
            extracted.append(out_path)
            print(f"[extract] Page {page_num} → {out_path.name}")
        else:
            print(f"[extract] Page {page_num} out of range (total: {len(doc)})")

    doc.close()
    return extracted


def extract_cover(ebook_path: str, output_path: str, dpi: int = 200) -> Optional[Path]:
    """Extract the first page as cover."""
    if pymupdf is None:
        raise ImportError("pymupdf not installed")

    doc = pymupdf.open(str(ebook_path))
    if len(doc) == 0:
        doc.close()
        return None

    zoom = dpi / 72.0
    mat = pymupdf.Matrix(zoom, zoom)
    pix = doc[0].get_pixmap(matrix=mat)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pix.save(str(output_path))
    doc.close()

    print(f"[extract] Cover → {output_path.name}")
    return output_path
