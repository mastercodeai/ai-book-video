"""
Main pipeline orchestrator for the ai-book-video skill.
Uses AI img2img for both page aging/annotation and cover generation.
"""

import sys
import json
import argparse
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent))

from utils import (
    setup_logging, load_env, find_input_images,
    get_image_dimensions, ensure_dir
)
from analyze_page import analyze_page, analyze_page_cached
from aging_engine import apply_aging_and_annotations
from cover_generator import generate_cover_prompt, generate_cover_image
from description_generator import generate_description_ai
from quality_checker import check_quality, generate_quality_report
from ebook_extractor import extract_ebook, find_ebook, EBOOK_EXTENSIONS


def parse_args():
    parser = argparse.ArgumentParser(
        description='AI Book Video Pipeline - Generate aged+annotated book page images'
    )
    parser.add_argument('--input-dir', type=str,
                        default=r'D:\Workspace\AI图书带货素材\原始图片')
    parser.add_argument('--ebook', type=str, default=None,
                        help='Path to ebook file (PDF/EPUB/MOBI). If set, extracts pages from ebook.')
    parser.add_argument('--ebook-dir', type=str,
                        default=r'D:\Workspace\AI图书带货素材\电子书',
                        help='Directory to scan for ebook files')
    parser.add_argument('--max-pages', type=int, default=20,
                        help='Max pages to extract from ebook (default 20)')
    parser.add_argument('--dpi', type=int, default=200,
                        help='DPI for ebook page extraction (default 200)')
    parser.add_argument('--output-dir', type=str, default=None)
    parser.add_argument('--font', type=str, default=r'C:\Windows\Fonts\simkai.ttf')
    parser.add_argument('--skip-cover', action='store_true')
    parser.add_argument('--skip-vision', action='store_true',
                        help='Skip vision analysis, use cached JSON')
    parser.add_argument('--book-name', type=str, default=None)
    parser.add_argument('--author', type=str, default='王克谦',
                        help='Book author name for description')
    parser.add_argument('--year', type=str, default='1984',
                        help='Publication year for description')
    parser.add_argument('--subject', type=str, default='英语',
                        help='Subject (英语/数学/etc) for description')
    return parser.parse_args()


def discover_images(input_dir: str) -> Dict:
    print("\n" + "=" * 60)
    print("STEP 1: Discovering input images")
    print("=" * 60)
    images = find_input_images(input_dir)
    if not images['pages']:
        raise FileNotFoundError(f"No page images found in {input_dir}")
    print(f"\n  Cover: {images['cover'].name if images['cover'] else 'Not found'}")
    print(f"  Pages: {len(images['pages'])} found")
    for i, page in enumerate(images['pages'][:5], 1):
        print(f"    {i}. {page.name}")
    if len(images['pages']) > 5:
        print(f"    ... and {len(images['pages']) - 5} more")
    return images


def create_output_structure(output_dir: Path) -> Dict[str, Path]:
    print("\n" + "=" * 60)
    print("STEP 2: Creating output directory structure")
    print("=" * 60)
    dirs = {
        'root': output_dir,
        'analysis': output_dir / 'analysis',
        'output': output_dir,
        'cover': output_dir,
    }
    for name, path in dirs.items():
        ensure_dir(path)
        print(f"  Created: {path}")
    return dirs


def process_single_page(
    page_path: Path,
    index: int,
    dirs: Dict[str, Path],
    config: Dict,
    skip_vision: bool = False
) -> Dict:
    page_name = page_path.stem
    print(f"\n--- Processing page {index}: {page_path.name} ---")

    result = {
        'page_path': str(page_path),
        'page_index': index,
        'success': False,
        'analysis': None,
        'quality': None,
        'error': None
    }

    try:
        # Step A: Vision analysis
        cache_path = dirs['analysis'] / f"{page_name}.json"

        if skip_vision and cache_path.exists():
            print(f"  [A] Loading cached analysis: {cache_path}")
            analysis = analyze_page_cached(str(cache_path))
        else:
            print(f"  [A] Running vision analysis...")
            analysis = analyze_page(str(page_path), config.get('vision', {}))
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, ensure_ascii=False, indent=2)
            print(f"  [A] Saved analysis: {cache_path}")

        result['analysis'] = analysis

        # Step B: AI img2img (aging + annotations in one call)
        output_path = dirs['output'] / f"{page_name}.png"
        print(f"  [B] AI img2img: aging + annotations...")
        apply_aging_and_annotations(
            str(page_path),
            analysis,
            str(output_path),
            config.get('image', {})
        )

        # Step C: Quality check
        print(f"  [C] Running quality check...")
        quality = check_quality(str(output_path), analysis)
        result['quality'] = quality

        result['success'] = True
        print(f"  ✓ Page {index} complete: {output_path.name}")

    except Exception as e:
        result['error'] = str(e)
        print(f"  ✗ Page {index} failed: {e}")

    return result


def generate_cover(
    cover_path: Optional[Path],
    page_analyses: List[Dict],
    book_name: str,
    dirs: Dict[str, Path],
    config: Dict
) -> Optional[str]:
    print("\n" + "=" * 60)
    print("STEP 4: Generating cover image (img2img)")
    print("=" * 60)

    if not cover_path or not cover_path.exists():
        print("  No cover image found, skipping")
        return None

    try:
        book_topic = book_name or (page_analyses[0].get('page_topic', '学习笔记') if page_analyses else '学习笔记')
        prompt = generate_cover_prompt(book_topic, page_analyses)

        # Save prompt
        prompt_path = dirs['cover'] / 'cover_prompt.txt'
        with open(prompt_path, 'w', encoding='utf-8') as f:
            f.write(prompt)

        output_path = dirs['cover'] / 'cover.png'
        generate_cover_image(
            str(cover_path),
            prompt,
            str(output_path),
            config.get('image', {})
        )

        print(f"  ✓ Cover generated: {output_path}")
        return str(output_path)

    except Exception as e:
        print(f"  ✗ Cover generation failed: {e}")
        return None


def print_summary(results, cover_path, dirs, start_time):
    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    print("PIPELINE SUMMARY")
    print("=" * 60)
    total = len(results)
    succeeded = sum(1 for r in results if r['success'])
    failed = total - succeeded
    print(f"\n  Total pages: {total}")
    print(f"  Succeeded:   {succeeded} ✅")
    print(f"  Failed:      {failed} ❌")
    print(f"  Cover:       {'Generated ✅' if cover_path else 'Skipped/Failed ❌'}")
    print(f"  Time:        {elapsed:.1f}s")
    print(f"\n  Output directory: {dirs['root']}")
    print(f"  Final images: {dirs['output']}")
    if failed > 0:
        print(f"\n  Failed pages:")
        for r in results:
            if not r['success']:
                print(f"    - Page {r['page_index']}: {r['error']}")
    print("\n" + "=" * 60)


def main():
    args = parse_args()
    setup_logging()
    start_time = time.time()

    print("\n" + "#" * 60)
    print("#  AI Book Video Pipeline (img2img mode)")
    print(f"#  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("#" * 60)

    load_env()

    # Determine output directory
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        from output_naming import make_output_dir, sanitize_book_name
        book_name = sanitize_book_name(args.book_name or 'book')
        base_dir = str(Path(args.input_dir).parent)
        output_dir = make_output_dir(base_dir, book_name)

    # Detect input mode: ebook or photo folder
    images = None

    # Priority 1: --ebook flag
    if args.ebook:
        ebook_path = Path(args.ebook)
        if not ebook_path.exists():
            raise FileNotFoundError(f"Ebook not found: {ebook_path}")
        print(f"\n📖 EBOOK MODE: {ebook_path.name}")
        images = extract_ebook(str(ebook_path), str(output_dir / '_raw'), args.dpi, args.max_pages)

    # Priority 2: scan ebook-dir for ebooks
    if images is None:
        ebook = find_ebook(args.ebook_dir)
        if ebook:
            print(f"\n📖 EBOOK MODE: {ebook.name} (found in {args.ebook_dir})")
            images = extract_ebook(str(ebook), str(output_dir / '_raw'), args.dpi, args.max_pages)

    # Priority 3: photo folder mode
    if images is None:
        images = discover_images(args.input_dir)

    dirs = create_output_structure(output_dir)

    config = {
        'vision': {},
        'image': {},
        'description': {
            'author': args.author,
            'year': args.year,
            'subject': args.subject,
        },
    }

    # Process each page
    print("\n" + "=" * 60)
    print("STEP 3: Processing pages (AI img2img)")
    print("=" * 60)

    results = []
    page_analyses = []

    for i, page_path in enumerate(images['pages'], 1):
        result = process_single_page(
            page_path, i, dirs, config,
            skip_vision=args.skip_vision
        )
        results.append(result)
        if result['analysis']:
            page_analyses.append(result['analysis'])

    # Generate cover
    cover_result = None
    if not args.skip_cover:
        cover_result = generate_cover(
            images['cover'], page_analyses, args.book_name or '', dirs, config
        )

    # Generate description
    print("\n" + "=" * 60)
    print("STEP 5: Generating text description")
    print("=" * 60)
    if page_analyses:
        description = generate_description_ai(
            args.book_name or '英语语法',
            page_analyses,
            config.get('description', {})
        )
        desc_path = dirs['root'] / '图文描述.txt'
        with open(desc_path, 'w', encoding='utf-8') as f:
            f.write(description)
        print(f"[desc] Saved: {desc_path}")
        print(f"[desc] Preview:\n{description[:200]}...")
    else:
        print("[desc] No page analyses available, skipping")

    # Quality report
    print("\n" + "=" * 60)
    print("STEP 6: Generating quality report")
    print("=" * 60)
    quality_results = [r['quality'] for r in results if r['quality'] is not None]
    if quality_results:
        generate_quality_report(quality_results, str(dirs['root'] / 'quality_report.md'))

    # Save manifest
    manifest = {
        'created': datetime.now().isoformat(),
        'input_dir': str(args.input_dir),
        'output_dir': str(output_dir),
        'book_name': args.book_name,
        'total_pages': len(images['pages']),
        'succeeded': sum(1 for r in results if r['success']),
        'cover_generated': cover_result is not None,
        'pages': [
            {
                'index': r['page_index'],
                'path': r['page_path'],
                'success': r['success'],
                'analysis': r['analysis']
            }
            for r in results
        ]
    }
    with open(dirs['root'] / 'manifest.json', 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print_summary(results, cover_result, dirs, start_time)


if __name__ == '__main__':
    main()
