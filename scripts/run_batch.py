"""
run_batch.py — 一键运行完整流程，无需审批。
用法: python3 run_batch.py --output-dir "输出目录路径" --book-name "书名" --author "作者" --subject "数学"
"""

import sys
import os
import json
import argparse
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from utils import load_env
from aging_engine import apply_aging_and_annotations
from cover_generator import generate_cover_prompt, generate_cover_image
from description_generator import generate_description_ai
from cleanup import cleanup_originals


def main():
    parser = argparse.ArgumentParser(description='Run book video pipeline')
    parser.add_argument('--output-dir', required=True, help='Output directory with analysis/ subfolder')
    parser.add_argument('--book-name', default='book', help='Book name')
    parser.add_argument('--author', default='', help='Author name')
    parser.add_argument('--subject', default='通用', help='Subject (英语/数学/语文/文言/物理/化学/通用)')
    parser.add_argument('--year', default='', help='Publication year')
    args = parser.parse_args()

    # Load env (proxy, API keys)
    load_env()

    # Set proxy (codeproxy.dev requires proxy to connect)
    if not os.environ.get('HTTPS_PROXY') and not os.environ.get('https_proxy'):
        os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7897'
        os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7897'

    out = Path(args.output_dir)
    analysis_dir = out / 'analysis'

    if not out.exists():
        print(f"ERROR: Output directory not found: {out}")
        sys.exit(1)

    # Find analysis files
    analysis_files = sorted(analysis_dir.glob('*.json'))
    if not analysis_files:
        print(f"ERROR: No analysis JSON files found in {analysis_dir}")
        sys.exit(1)

    print(f"Book: {args.book_name}")
    print(f"Author: {args.author}")
    print(f"Subject: {args.subject}")
    print(f"Output: {out}")
    print(f"Pages: {len(analysis_files)}")
    print("=" * 50)

    # Process each page
    page_analyses = []
    for af in analysis_files:
        page_num = af.stem  # e.g., "1", "2", "3"
        img_path = out / f'{page_num}.jpg'

        if not img_path.exists():
            print(f"WARNING: Image not found: {img_path}, skipping")
            continue

        with open(af, 'r', encoding='utf-8') as f:
            analysis = json.load(f)

        page_analyses.append(analysis)
        output_path = out / f'{page_num}.png'

        print(f"\nPage {page_num}: {analysis.get('page_topic', 'unknown')}")
        apply_aging_and_annotations(
            str(img_path), analysis, str(output_path),
            subject=args.subject
        )

    # Generate cover
    print("\n" + "=" * 50)
    print("Generating cover...")
    cover_src = None
    for pattern in ['封面*.jpg', '封面*.jpeg', '封面*.png']:
        matches = list(out.glob(pattern))
        if matches:
            cover_src = matches[0]
            break

    if cover_src and cover_src.exists():
        config = {
            'author': args.author,
            'year': args.year,
            'subject': args.subject,
        }
        prompt = generate_cover_prompt(args.book_name, page_analyses, config)
        cover_out = out / 'cover.png'
        generate_cover_image(str(cover_src), prompt, str(cover_out))
    else:
        print("WARNING: Cover image not found, skipping")

    # Generate description
    print("\n" + "=" * 50)
    print("Generating description...")
    desc = generate_description_ai(
        args.book_name, page_analyses,
        {'author': args.author, 'year': args.year, 'subject': args.subject}
    )
    desc_path = out / '图文描述.txt'
    with open(desc_path, 'w', encoding='utf-8') as f:
        f.write(desc)
    print(f"Description saved ({len(desc)} chars)")

    # Cleanup
    print("\n" + "=" * 50)
    print("Cleaning up...")
    cleanup_originals(str(out))

    # Summary
    print("\n" + "=" * 50)
    print("DONE!")
    print(f"Output: {out}")
    final_files = [f.name for f in out.iterdir() if f.is_file()]
    for f in sorted(final_files):
        print(f"  {f}")


if __name__ == '__main__':
    main()
