"""
Page tracker — tracks which content pages have been used across runs
for the same book, ensuring each run uses different pages.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional


def get_tracker_path(ebook_path: str, output_dir: str) -> Path:
    """Get the path to the used_pages tracker file for a book."""
    # Use book filename as key
    book_key = Path(ebook_path).stem[:50]  # Limit length
    tracker_dir = Path(output_dir).parent
    return tracker_dir / f'.used_pages_{book_key}.json'


def load_used_pages(tracker_path: Path) -> Dict:
    """Load the used pages tracker."""
    if tracker_path.exists():
        with open(tracker_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'used_pages': [], 'runs': []}


def save_used_pages(tracker_path: Path, tracker: Dict):
    """Save the used pages tracker."""
    tracker_path.parent.mkdir(parents=True, exist_ok=True)
    with open(tracker_path, 'w', encoding='utf-8') as f:
        json.dump(tracker, f, ensure_ascii=False, indent=2)


def select_unused_pages(
    content_pages: List[int],
    used_pages: List[int],
    count: int = 3,
) -> List[int]:
    """
    Select unused content pages for this run.

    Args:
        content_pages: List of all available content page numbers.
        used_pages: List of already used page numbers.
        count: Number of pages to select.

    Returns:
        List of selected page numbers.
    """
    available = [p for p in content_pages if p not in used_pages]

    if len(available) < count:
        print(f"[tracker] Warning: only {len(available)} unused pages available (need {count})")
        # If we've used all pages, reset and allow reuse
        if len(available) == 0:
            print("[tracker] All pages used, resetting tracker for this book")
            available = content_pages

    # Take first N available pages
    selected = available[:count]
    return selected


def mark_pages_used(
    tracker_path: Path,
    page_numbers: List[int],
    run_id: str,
):
    """Mark pages as used in the tracker."""
    tracker = load_used_pages(tracker_path)

    for p in page_numbers:
        if p not in tracker['used_pages']:
            tracker['used_pages'].append(p)

    tracker['runs'].append({
        'run_id': run_id,
        'pages': page_numbers,
    })

    save_used_pages(tracker_path, tracker)
    print(f"[tracker] Marked pages {page_numbers} as used (total used: {len(tracker['used_pages'])})")
