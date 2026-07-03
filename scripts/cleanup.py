"""
Post-processing cleanup: remove original input files from output directory
after successful generation, keeping only final PNG outputs and description.
"""

import os
from pathlib import Path
from typing import List


def cleanup_originals(output_dir: str, keep_extensions: List[str] = None):
    """
    Remove original input files (JPG, analysis JSON, etc.) from output directory.
    Keeps only final PNG images and text description.

    Args:
        output_dir: Path to the output directory.
        keep_extensions: File extensions to keep (default: .png, .txt)
    """
    if keep_extensions is None:
        keep_extensions = ['.png', '.txt']

    output_dir = Path(output_dir)
    removed = []

    for f in output_dir.iterdir():
        if f.is_file() and f.suffix.lower() not in keep_extensions:
            f.unlink()
            removed.append(f.name)

    # Also remove subdirectories (analysis, _raw, _scan, etc.)
    for d in output_dir.iterdir():
        if d.is_dir():
            import shutil
            shutil.rmtree(str(d), ignore_errors=True)
            removed.append(f"{d.name}/")

    if removed:
        print(f"[cleanup] Removed {len(removed)} items: {', '.join(removed[:5])}{'...' if len(removed) > 5 else ''}")
    else:
        print("[cleanup] Nothing to clean up")
