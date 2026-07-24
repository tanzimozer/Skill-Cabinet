#!/usr/bin/env python3
"""
verify_pdf.py — Post-render verification for Linked Engine outputs

Usage: python3 verify_pdf.py output/LE###/filename.pdf

Checks:
1. Single page (hard requirement)
2. No margin violations (left < 40, right > 572)
3. Content doesn't overlap footer (y < 38)
4. PNG exists and has correct dimensions
"""

import sys
import os

def verify(pdf_path):
    try:
        import fitz
    except ImportError:
        print("Error: PyMuPDF not installed. Run: pip install pymupdf")
        sys.exit(1)
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF not found: {pdf_path}")
        sys.exit(1)
    
    doc = fitz.open(pdf_path)
    errors = []
    warnings = []
    
    # Check 1: Single page
    if doc.page_count != 1:
        errors.append(f"PDF has {doc.page_count} pages, expected 1")
    
    page = doc[0]
    MARGIN_L = 40
    MARGIN_R = 572
    FLOOR = 38
    
    # Check 2: Margin violations
    for b in page.get_text('dict')['blocks']:
        for line in b.get('lines', []):
            for span in line['spans']:
                bbox = span['bbox']
                text = span['text'][:30]
                if bbox[0] < MARGIN_L - 1:  # 1pt tolerance
                    errors.append(f"LEFT MARGIN: '{text}' at x={bbox[0]:.1f}")
                if bbox[2] > MARGIN_R + 1:
                    errors.append(f"RIGHT MARGIN: '{text}' at x={bbox[2]:.1f}")
    
    # Check 3: Footer overlap
    content_blocks = [b for b in page.get_text('dict')['blocks'] if 'lines' in b]
    if content_blocks:
        lowest_content = min(b['bbox'][1] for b in content_blocks)
        if lowest_content < FLOOR:
            warnings.append(f"Content at y={lowest_content:.1f} near footer (floor={FLOOR})")
    
    # Check 4: PNG exists
    png_path = pdf_path.replace('.pdf', '.png')
    if not os.path.exists(png_path):
        warnings.append(f"PNG not found at {png_path}")
    else:
        try:
            from PIL import Image
            img = Image.open(png_path)
            if img.size != (2550, 3300):  # US Letter at 300 DPI
                warnings.append(f"PNG size {img.size}, expected (2550, 3300)")
        except ImportError:
            pass
    
    # Report
    print(f"\n{'='*50}")
    print(f"VERIFY: {pdf_path}")
    print(f"{'='*50}")
    
    if errors:
        print(f"\n❌ ERRORS ({len(errors)}):")
        for e in errors:
            print(f"   • {e}")
    
    if warnings:
        print(f"\n⚠️ WARNINGS ({len(warnings)}):")
        for w in warnings:
            print(f"   • {w}")
    
    if not errors and not warnings:
        print("\n✅ ALL CHECKS PASSED")
    
    print()
    
    sys.exit(1 if errors else 0)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 verify_pdf.py <pdf_path>")
        sys.exit(1)
    verify(sys.argv[1])
