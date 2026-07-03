"""
Output folder naming utility.
Format: {书名}_{YYYYMMDD}_{两位流水号}
流水号每天重置。
"""

from pathlib import Path
from datetime import datetime
from typing import Optional


def get_next_sequence(base_dir: str, book_name: str, date_str: Optional[str] = None) -> int:
    """
    Get the next sequence number for a given book and date.

    Args:
        base_dir: Base output directory (e.g., D:\Workspace\AI图书带货素材)
        book_name: Book name for folder prefix
        date_str: Date string in YYYYMMDD format (default: today)

    Returns:
        Next sequence number (1, 2, 3, ...)
    """
    if date_str is None:
        date_str = datetime.now().strftime('%Y%m%d')

    base_path = Path(base_dir)
    if not base_path.exists():
        return 1

    # Find existing folders matching pattern: {book_name}_{date}_*
    pattern = f"{book_name}_{date_str}_*"
    existing = list(base_path.glob(pattern))

    if not existing:
        return 1

    # Extract sequence numbers from existing folders
    max_seq = 0
    for folder in existing:
        name = folder.name
        # Expected format: bookname_YYYYMMDD_XX
        parts = name.rsplit('_', 1)
        if len(parts) == 2:
            try:
                seq = int(parts[1])
                max_seq = max(max_seq, seq)
            except ValueError:
                continue

    return max_seq + 1


def make_output_dir(base_dir: str, book_name: str) -> Path:
    """
    Create output directory with naming convention: {书名}_{YYYYMMDD}_{两位流水号}

    Args:
        base_dir: Base output directory
        book_name: Book name

    Returns:
        Path to the created output directory
    """
    today = datetime.now().strftime('%Y%m%d')
    seq = get_next_sequence(base_dir, book_name, today)
    seq_str = f"{seq:02d}"

    dir_name = f"{book_name}_{today}_{seq_str}"
    output_path = Path(base_dir) / dir_name
    output_path.mkdir(parents=True, exist_ok=True)

    return output_path


def sanitize_book_name(book_name: str) -> str:
    """
    Sanitize book name for use in folder names.
    Remove special characters, keep Chinese/English/numbers.
    """
    import re
    # Keep Chinese characters, English letters, numbers, and underscores
    sanitized = re.sub(r'[^\u4e00-\u9fff\w]', '', book_name)
    # Limit length
    if len(sanitized) > 20:
        sanitized = sanitized[:20]
    return sanitized
