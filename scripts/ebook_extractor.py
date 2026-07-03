"""
Ebook page extractor — extracts pages from PDF/EPUB/MOBI as images.
Uses pymupdf for PDF, and calibre (ebook-convert) for EPUB/MOBI → PDF first.
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional


# Supported ebook extensions
EBOOK_EXTENSIONS = {'.pdf', '.epub', '.mobi', '.azw3', '.azw', '.fb2'}


def find_ebook(input_dir: str) -> Optional[Path]:
    """Find an ebook file in the input directory."""
    input_path = Path(input_dir)
    for ext in EBOOK_EXTENSIONS:
        matches = list(input_path.glob(f'*{ext}')) + list(input_path.glob(f'*{ext.upper()}'))
        if matches:
            return matches[0]
    return None


def convert_to_pdf(ebook_path: Path, output_pdf: Path) -> Path:
    """
    Convert EPUB/MOBI/AZW3 to PDF using calibre's ebook-convert.
    """
    calibre_paths = [
        r'D:\Software\calibre\ebook-convert.exe',
        r'C:\Program Files\Calibre2\ebook-convert.exe',
        r'C:\Program Files (x86)\Calibre2\ebook-convert.exe',
    ]

    # Also check PATH
    calibre_cmd = None
    for p in calibre_paths:
        if Path(p).exists():
            calibre_cmd = p
            break

    if not calibre_cmd:
        # Try from PATH
        try:
            result = subprocess.run(['ebook-convert', '--version'],
                                    capture_output=True, timeout=10)
            if result.returncode == 0:
                calibre_cmd = 'ebook-convert'
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

    if not calibre_cmd:
        raise FileNotFoundError(
            "calibre not found. Install from https://calibre-ebook.com or "
            "set path manually. Expected at D:\\Software\\calibre\\ebook-convert.exe"
        )

    print(f"[ebook] Converting {ebook_path.name} to PDF...")
    cmd = [
        calibre_cmd,
        str(ebook_path),
        str(output_pdf),
        '--pdf-add-toc',
        '--pdf-page-numbers',
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        raise RuntimeError(f"ebook-convert failed: {result.stderr[:500]}")

    if not output_pdf.exists():
        raise RuntimeError(f"PDF not created at {output_pdf}")

    print(f"[ebook] Converted to PDF: {output_pdf}")
    return output_pdf


def extract_pages_from_pdf(pdf_path: Path, output_dir: Path, dpi: int = 200) -> List[Path]:
    """
    Extract each page from a PDF as a PNG image using pymupdf.

    Args:
        pdf_path: Path to the PDF file.
        output_dir: Directory to save page images.
        dpi: Resolution for rendering (default 200).

    Returns:
        List of paths to extracted page images.
    """
    try:
        import pymupdf
    except ImportError:
        raise ImportError("pymupdf not installed. Run: uv pip install pymupdf")

    output_dir.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(str(pdf_path))

    page_paths = []
    total = len(doc)
    print(f"[ebook] Extracting {total} pages from {pdf_path.name} (DPI={dpi})...")

    for i in range(total):
        page = doc[i]
        # Render page as image
        zoom = dpi / 72.0  # 72 is default DPI
        mat = pymupdf.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)

        output_path = output_dir / f"{i + 1}.png"
        pix.save(str(output_path))
        page_paths.append(output_path)

        if (i + 1) % 10 == 0 or i == total - 1:
            print(f"[ebook]   {i + 1}/{total} pages extracted")

    doc.close()
    print(f"[ebook] All {total} pages saved to {output_dir}")
    return page_paths


def extract_cover_from_pdf(pdf_path: Path, output_path: Path, dpi: int = 200) -> Optional[Path]:
    """
    Extract the first page of a PDF as the cover image.
    """
    try:
        import pymupdf
    except ImportError:
        raise ImportError("pymupdf not installed. Run: uv pip install pymupdf")

    doc = pymupdf.open(str(pdf_path))
    if len(doc) == 0:
        doc.close()
        return None

    page = doc[0]
    zoom = dpi / 72.0
    mat = pymupdf.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    pix.save(str(output_path))
    doc.close()

    print(f"[ebook] Cover extracted: {output_path}")
    return output_path


def extract_ebook(
    ebook_path: str,
    output_dir: str,
    dpi: int = 200,
    max_pages: int = 20
) -> dict:
    """
    Main entry point: extract pages from any supported ebook format.

    Args:
        ebook_path: Path to the ebook file.
        output_dir: Directory to save extracted images.
        dpi: Rendering resolution.
        max_pages: Maximum number of pages to extract (skip cover).

    Returns:
        Dict with 'cover' (Path or None) and 'pages' (list of Paths).
    """
    ebook_path = Path(ebook_path)
    output_dir = Path(output_dir)
    temp_dir = None

    if not ebook_path.exists():
        raise FileNotFoundError(f"Ebook not found: {ebook_path}")

    ext = ebook_path.suffix.lower()

    # If not PDF, convert first
    if ext != '.pdf':
        temp_dir = Path(tempfile.mkdtemp(prefix='ebook_'))
        pdf_path = temp_dir / f"{ebook_path.stem}.pdf"
        convert_to_pdf(ebook_path, pdf_path)
    else:
        pdf_path = ebook_path

    # Extract cover (page 0)
    cover_path = output_dir / "封面.png"
    cover = extract_cover_from_pdf(pdf_path, cover_path, dpi)

    # Extract content pages (skip first page = cover, limit to max_pages)
    all_pages_dir = output_dir / "_all_pages"
    all_pages = extract_pages_from_pdf(pdf_path, all_pages_dir, dpi)

    # Skip cover page (index 0), take up to max_pages
    content_pages = all_pages[1:max_pages + 1] if len(all_pages) > 1 else all_pages

    # Rename content pages to 1.png, 2.png, etc. in the main output dir
    page_paths = []
    for i, src in enumerate(content_pages, 1):
        dst = output_dir / f"{i}.png"
        if src != dst:
            import shutil
            shutil.copy2(str(src), str(dst))
        page_paths.append(dst)

    # Clean up temp all_pages dir
    import shutil
    if all_pages_dir.exists():
        shutil.rmtree(str(all_pages_dir), ignore_errors=True)

    # Clean up temp PDF
    if temp_dir and temp_dir.exists():
        shutil.rmtree(str(temp_dir), ignore_errors=True)

    print(f"[ebook] Ready: {len(page_paths)} pages + cover")

    return {
        'cover': cover,
        'pages': page_paths,
    }
