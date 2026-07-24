#!/usr/bin/env python3
"""
Deep color extraction with per-screen averages and lightness analysis.
Use when precise color matching is critical.
"""

from PIL import Image
import colorsys
from collections import Counter

def deep_extract(path, name, hue_range=(20, 55)):
    """
    Extract accent colors in a specific hue range with detailed analysis.
    
    Args:
        path: Image file path
        name: Screen name for reporting
        hue_range: Tuple (min_hue, max_hue) in degrees for accent detection
    
    Returns:
        Dict with top colors, average, and distribution
    """
    img = Image.open(path).convert('RGB')
    width, height = img.size
    
    accent_pixels = []  # Pixels in the target hue range
    
    for y in range(height):
        for x in range(width):
            r, g, b = img.getpixel((x, y))
            h, l, s = colorsys.rgb_to_hls(r/255, g/255, b/255)
            h_deg = h * 360
            s_pct = s * 100
            l_pct = l * 100
            
            # Filter for accent hue range (e.g., gold = 20-55°)
            if hue_range[0] <= h_deg <= hue_range[1] and s_pct > 15 and l_pct > 25:
                accent_pixels.append((r, g, b, h_deg, s_pct, l_pct))
    
    if not accent_pixels:
        print(f"{name}: No accent colors found in hue range {hue_range}")
        return None
    
    # Bucket and count
    def bucket(rgb):
        return (rgb[0]//4*4, rgb[1]//4*4, rgb[2]//4*4)
    
    counts = Counter(bucket((r, g, b)) for r, g, b, *_ in accent_pixels)
    top10 = counts.most_common(10)
    
    # Calculate average
    avg_r = sum(p[0] for p in accent_pixels) // len(accent_pixels)
    avg_g = sum(p[1] for p in accent_pixels) // len(accent_pixels)
    avg_b = sum(p[2] for p in accent_pixels) // len(accent_pixels)
    avg_h, avg_l, avg_s = colorsys.rgb_to_hls(avg_r/255, avg_g/255, avg_b/255)
    
    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"{'='*60}")
    print(f"Total accent pixels: {len(accent_pixels)}")
    print(f"\nAVERAGE: #{avg_r:02X}{avg_g:02X}{avg_b:02X} (H={avg_h*360:.1f}° S={avg_s*100:.1f}% L={avg_l*100:.1f}%)")
    print(f"\nTOP 10 BY FREQUENCY:")
    
    for (r, g, b), count in top10:
        h, l, s = colorsys.rgb_to_hls(r/255, g/255, b/255)
        print(f"  #{r:02X}{g:02X}{b:02X}  {count:>5} px  H={h*360:5.1f}° S={s*100:4.1f}% L={l*100:4.1f}%")
    
    return {
        'name': name,
        'total_pixels': len(accent_pixels),
        'average': (avg_r, avg_g, avg_b),
        'average_hsl': (avg_h*360, avg_s*100, avg_l*100),
        'top10': top10
    }


def analyze_references(paths_and_names, hue_range=(20, 55)):
    """
    Analyze multiple reference screenshots and recommend primary color.
    
    Args:
        paths_and_names: List of (path, name) tuples
        hue_range: Hue range for accent detection
    """
    results = []
    
    for path, name in paths_and_names:
        result = deep_extract(path, name, hue_range)
        if result:
            results.append(result)
    
    if not results:
        print("No results to analyze")
        return
    
    # Sort by lightness
    print(f"\n{'='*60}")
    print("  PER-SCREEN AVERAGES (sorted by lightness)")
    print(f"{'='*60}")
    
    sorted_by_l = sorted(results, key=lambda r: r['average_hsl'][2])
    
    for r in sorted_by_l:
        avg_r, avg_g, avg_b = r['average']
        h, s, l = r['average_hsl']
        print(f"  {r['name']:20} #{avg_r:02X}{avg_g:02X}{avg_b:02X}  L={l:.1f}%")
    
    # Recommendation: use the middle-dark value
    mid_idx = len(sorted_by_l) // 2
    rec = sorted_by_l[mid_idx]
    avg_r, avg_g, avg_b = rec['average']
    
    print(f"\n{'='*60}")
    print(f"  RECOMMENDATION: #{avg_r:02X}{avg_g:02X}{avg_b:02X}")
    print(f"  (middle of the lightness range — not too bright, not too dark)")
    print(f"{'='*60}")


# Example usage:
if __name__ == "__main__":
    # Replace with actual paths
    refs = [
        ("/path/to/move_money.jpg", "Move Money"),
        ("/path/to/net_worth.jpg", "Net Worth"),
        ("/path/to/family.jpg", "Family"),
        ("/path/to/gold_card.jpg", "Gold Card"),
        ("/path/to/virtual_cards.jpg", "Virtual Cards"),
    ]
    
    # For gold detection (H=20-55°)
    analyze_references(refs, hue_range=(20, 55))
