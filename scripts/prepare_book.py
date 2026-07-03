"""
prepare_book.py — Scan ebook, identify content pages, select unused pages,
extract them for processing.

Usage:
  python3 prepare_book.py --ebook "path/to/book.pdf" --book-name "书名"

Output:
  - Prints page type analysis for first N pages
  - Selects unused content pages
  - Extracts cover + selected pages to output directory
  - Prints which pages need vision analysis

The Hermes agent then:
  1. Uses vision_analyze on the extracted pages
  2. Saves analysis JSONs
  3. Runs pipeline.py --skip-vision
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from ebook_scanner import scan_ebook_pages, extract_content_pages, extract_cover
from page_tracker import (
    get_tracker_path, load_used_pages, save_used_pages,
    select_unused_pages, mark_pages_used
)


def parse_args():
    parser = argparse.ArgumentParser(description='Prepare book for processing')
    parser.add_argument('--ebook', type=str, required=True, help='Path to ebook file')
    parser.add_argument('--book-name', type=str, default=None, help='Book name')
    parser.add_argument('--output-dir', type=str, default=None, help='Output directory')
    parser.add_argument('--pages', type=int, default=3, help='Number of content pages to select')
    parser.add_argument('--content-pages', type=str, default=None,
                        help='Comma-separated content page numbers (e.g., 7,8,9). Skip scan if provided.')
    parser.add_argument('--scan-range', type=int, default=15, help='Pages to scan for type detection')
    parser.add_argument('--dpi', type=int, default=200, help='DPI for page extraction')
    return parser.parse_args()


def main():
    args = parse_args()
    ebook_path = Path(args.ebook)

    if not ebook_path.exists():
        print(f"ERROR: Ebook not found: {ebook_path}")
        sys.exit(1)

    book_name = args.book_name or ebook_path.stem[:30]
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = Path(r'D:\Workspace\AI图书带货素材') / f'{book_name}_{timestamp}'

    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print(f"PREPARING BOOK: {book_name}")
    print(f"Ebook: {ebook_path.name}")
    print(f"Output: {output_dir}")
    print("=" * 60)

    # Step 1: Scan pages (skip if --content-pages provided)
    if args.content_pages:
        print("\n--- Using provided content pages ---")
        content_pages = [int(p.strip()) for p in args.content_pages.split(',')]
        print(f"Content pages: {content_pages}")

        # Still extract cover
        raw_dir = output_dir / '_raw'
        raw_dir.mkdir(parents=True, exist_ok=True)
        scan_dir = output_dir / '_scan'
        scan_dir.mkdir(parents=True, exist_ok=True)

        # Scan first page for cover detection
        scan_result = scan_ebook_pages(
            str(ebook_path), str(output_dir),
            scan_range=1, dpi=args.dpi,
        )
    else:
        print("\n--- Step 1: Scanning pages ---")
        scan_result = scan_ebook_pages(
            str(ebook_path), str(output_dir),
            scan_range=args.scan_range, dpi=args.dpi,
        )

        # Step 2: Identify content pages from scan
        print("\n--- Step 2: Identifying content pages ---")
        content_pages = []
        for p in scan_result['scanned_pages']:
            if p['is_likely_content']:
                content_pages.append(p['page_num'])

        # For scanned PDFs where heuristic fails, use all non-front pages
        if not content_pages:
            print("[scan] Heuristic found no content pages (likely scanned PDF)")
            print("[scan] Will need vision analysis to identify page types")
            print("[scan] Scan images saved for manual/vision review:")
            for p in scan_result['scanned_pages']:
                print(f"  Page {p['page_num']}: {p['image_path']}")

            print("\n" + "=" * 60)
            print("HERMES AGENT: Use vision_analyze to identify page types")
            print("=" * 60)
            print("\nFor each scanned page, ask vision_analyze:")
            print("  'What type is this page: cover/copyright/preface/TOC/content/exercise?'")
            print("\nThen run prepare_book again with --content-pages flag:")
            print(f"  python3 prepare_book.py --ebook '{ebook_path}' --content-pages 7,8,9")
            return None

        print(f"Content pages: {content_pages}")
        print(f"Content starts at page: {scan_result['content_start_page']}")

    # Step 3: Load tracker and select unused pages
    print("\n--- Step 3: Selecting pages ---")
    tracker_path = get_tracker_path(str(ebook_path), str(output_dir))
    tracker = load_used_pages(tracker_path)
    print(f"Previously used pages: {tracker['used_pages']}")

    selected = select_unused_pages(
        content_pages,
        tracker['used_pages'],
        count=args.pages,
    )
    print(f"Selected pages for this run: {selected}")

    if not selected:
        print("ERROR: No content pages available")
        sys.exit(1)

    # Step 4: Extract cover + selected pages
    print("\n--- Step 4: Extracting pages ---")
    raw_dir = output_dir / '_raw'
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Extract cover
    cover_path = extract_cover(str(ebook_path), str(raw_dir / '封面.png'), args.dpi)

    # Extract selected content pages
    page_paths = extract_content_pages(
        str(ebook_path),
        raw_dir,
        selected,
        args.dpi,
    )

    # Step 5: Mark pages as used
    run_id = f"{book_name}_{timestamp}"
    mark_pages_used(tracker_path, selected, run_id)

    # Step 6: Output summary
    print("\n" + "=" * 60)
    print("PREPARATION COMPLETE")
    print("=" * 60)
    print(f"\nCover: {cover_path}")
    print(f"Content pages extracted: {len(page_paths)}")
    for i, (page_num, path) in enumerate(zip(selected, page_paths), 1):
        print(f"  {i}. Page {page_num} → {path.name}")

    print(f"\nPage scan images: {output_dir / '_scan'}")
    print(f"Extracted pages: {raw_dir}")

    # Create analysis directory
    analysis_dir = output_dir / 'analysis'
    analysis_dir.mkdir(parents=True, exist_ok=True)

    # Output instructions for Hermes agent
    print("\n" + "=" * 60)
    print("NEXT STEPS FOR HERMES AGENT:")
    print("=" * 60)
    print(f"\n1. Use vision_analyze on these pages to extract content:")
    for i, (page_num, path) in enumerate(zip(selected, page_paths), 1):
        print(f"   vision_analyze('{path}', 'read this page and extract key text...')")
    print(f"\n2. Save analysis JSONs to: {analysis_dir}")
    print(f"\n3. Run pipeline:")
    print(f"   python3 pipeline.py --skip-vision --output-dir '{output_dir}' --book-name '{book_name}'")

    # Save preparation manifest
    manifest = {
        'book_name': book_name,
        'ebook_path': str(ebook_path),
        'output_dir': str(output_dir),
        'selected_pages': selected,
        'cover_path': str(cover_path),
        'page_paths': [str(p) for p in page_paths],
        'analysis_dir': str(analysis_dir),
        'scan_result': scan_result,
    }
    manifest_path = output_dir / 'prepare_manifest.json'
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    return manifest


if __name__ == '__main__':
    main()
