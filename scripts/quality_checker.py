"""
Quality validation module for checking generated images and analysis data.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


def check_quality(image_path: str, analysis_data: Optional[Dict] = None) -> Dict:
    """
    Check quality of a generated image and its analysis data.
    
    Args:
        image_path: Path to the image file.
        analysis_data: Optional analysis dict to validate.
    
    Returns:
        Dict with check results:
            - passed: bool, overall pass/fail
            - checks: dict of individual check results
            - issues: list of issue descriptions
    """
    result = {
        'image_path': str(image_path),
        'passed': True,
        'checks': {},
        'issues': []
    }
    
    image_path = Path(image_path)
    
    # Check 1: File exists and has reasonable size
    try:
        file_size = image_path.stat().st_size
        min_size = 100 * 1024  # 100KB
        size_ok = file_size > min_size
        result['checks']['file_size'] = {
            'value': file_size,
            'threshold': min_size,
            'passed': size_ok
        }
        if not size_ok:
            result['issues'].append(f"File size ({file_size} bytes) is below threshold ({min_size} bytes)")
            result['passed'] = False
    except Exception as e:
        result['checks']['file_size'] = {'passed': False, 'error': str(e)}
        result['issues'].append(f"Could not check file size: {e}")
        result['passed'] = False
    
    # Check 2: Image dimensions
    try:
        from PIL import Image
        with Image.open(image_path) as img:
            width, height = img.size
            min_dimension = 500
            dims_ok = width > min_dimension and height > min_dimension
            result['checks']['dimensions'] = {
                'width': width,
                'height': height,
                'threshold': min_dimension,
                'passed': dims_ok
            }
            if not dims_ok:
                result['issues'].append(f"Image dimensions ({width}x{height}) below threshold ({min_dimension}px)")
                result['passed'] = False
    except Exception as e:
        result['checks']['dimensions'] = {'passed': False, 'error': str(e)}
        result['issues'].append(f"Could not check dimensions: {e}")
        result['passed'] = False
    
    # Check 3: Analysis data validation (if provided)
    if analysis_data:
        # Check bbox bounds
        bbox = analysis_data.get('bbox', {})
        if bbox:
            bbox_ok = True
            for key in ['x1', 'y1', 'x2', 'y2']:
                val = bbox.get(key, -1)
                if not (0 < val < 1):
                    bbox_ok = False
                    result['issues'].append(f"bbox.{key} = {val} is out of bounds (0-1)")
            
            result['checks']['bbox_bounds'] = {
                'bbox': bbox,
                'passed': bbox_ok
            }
            if not bbox_ok:
                result['passed'] = False
        
        # Check annotation text length (2-4 chars)
        annotation = analysis_data.get('annotation', '')
        annotation_len = len(annotation)
        annotation_ok = 2 <= annotation_len <= 4
        result['checks']['annotation_length'] = {
            'value': annotation,
            'length': annotation_len,
            'min': 2,
            'max': 4,
            'passed': annotation_ok
        }
        if not annotation_ok:
            result['issues'].append(f"Annotation text '{annotation}' length ({annotation_len}) not in range 2-4")
            # Don't fail overall for this - it's a soft check
        
        # Check key_text exists
        key_text = analysis_data.get('key_text', '')
        key_text_ok = len(key_text) > 0
        result['checks']['key_text'] = {
            'exists': key_text_ok,
            'length': len(key_text),
            'passed': key_text_ok
        }
        if not key_text_ok:
            result['issues'].append("Missing key_text in analysis data")
            result['passed'] = False
    
    # Summary
    result['total_checks'] = len(result['checks'])
    result['passed_checks'] = sum(1 for c in result['checks'].values() if c.get('passed', False))
    
    status = "PASS" if result['passed'] else "FAIL"
    print(f"[quality] {status} - {image_path.name} ({result['passed_checks']}/{result['total_checks']} checks passed)")
    
    return result


def generate_quality_report(results_list: List[Dict], output_path: str) -> str:
    """
    Generate a markdown quality report from check results.
    
    Args:
        results_list: List of check_quality result dicts.
        output_path: Path to save the report.
    
    Returns:
        Path to the saved report.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Calculate summary stats
    total = len(results_list)
    passed = sum(1 for r in results_list if r.get('passed', False))
    failed = total - passed
    
    # Generate report
    lines = []
    lines.append("# Quality Report")
    lines.append("")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Total Images | {total} |")
    lines.append(f"| Passed | {passed} ✅ |")
    lines.append(f"| Failed | {failed} ❌ |")
    lines.append(f"| Pass Rate | {passed/total*100:.1f}% |" if total > 0 else "| Pass Rate | N/A |")
    lines.append("")
    
    if failed > 0:
        lines.append("## Failed Images")
        lines.append("")
        for result in results_list:
            if not result.get('passed', False):
                lines.append(f"### {Path(result.get('image_path', 'unknown')).name}")
                lines.append("")
                for issue in result.get('issues', []):
                    lines.append(f"- ❌ {issue}")
                lines.append("")
    
    lines.append("## Detailed Results")
    lines.append("")
    lines.append("| Image | Status | Size Check | Dims Check | Annotation |")
    lines.append("|-------|--------|------------|------------|------------|")
    
    for result in results_list:
        name = Path(result.get('image_path', 'unknown')).name
        status = "✅" if result.get('passed', False) else "❌"
        checks = result.get('checks', {})
        
        size_status = "✅" if checks.get('file_size', {}).get('passed', False) else "❌"
        dims_status = "✅" if checks.get('dimensions', {}).get('passed', False) else "❌"
        annot_status = "✅" if checks.get('annotation_length', {}).get('passed', False) else "⚠️"
        
        lines.append(f"| {name} | {status} | {size_status} | {dims_status} | {annot_status} |")
    
    lines.append("")
    lines.append("---")
    lines.append("*Report generated by ai-book-video quality checker*")
    
    report_text = "\n".join(lines)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_text)
    
    print(f"[quality] Report saved to: {output_path}")
    return str(output_path)
