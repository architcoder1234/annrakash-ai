"""
check_contrast.py - WCAG 2.1 Color Contrast Ratio Validator for AnnRakshak AI
Calculates relative luminance and contrast ratio for all 3 themes
to guarantee accessibility compliance (>= 4.5:1 for normal body text, >= 3.0:1 for large text/borders).
"""

import math

def hex_to_rgb(hex_str: str):
    hex_str = hex_str.lstrip('#')
    if len(hex_str) == 3:
        hex_str = ''.join([c*2 for c in hex_str])
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

def get_relative_luminance(rgb):
    # WCAG 2.1 formula
    rgb_normalized = []
    for c in rgb:
        val = c / 255.0
        if val <= 0.04045:
            rgb_normalized.append(val / 12.92)
        else:
            rgb_normalized.append(math.pow((val + 0.055) / 1.055, 2.4))
    r, g, b = rgb_normalized
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def calculate_contrast_ratio(hex1: str, hex2: str) -> float:
    lum1 = get_relative_luminance(hex_to_rgb(hex1))
    lum2 = get_relative_luminance(hex_to_rgb(hex2))
    l_max = max(lum1, lum2)
    l_min = min(lum1, lum2)
    return (l_max + 0.05) / (l_min + 0.05)

def check_all_themes():
    checks = [
        # Theme: AnnRakshak Nature (Light)
        ("Nature: Body Text on Background", "#0F172A", "#FBF9F4", 4.5),
        ("Nature: Secondary Text on Background", "#334155", "#FBF9F4", 4.5),
        ("Nature: Darkened Orange Accent on Card", "#A23B20", "#FFFFFF", 4.5),
        ("Nature: Primary Forest on White", "#1B4332", "#FFFFFF", 4.5),
        ("Nature: Card Body on Card Surface", "#0F172A", "#FFFFFF", 4.5),

        # Theme: Midnight Pro (Dark)
        ("Midnight: Primary Text on Dark Canvas", "#F8FAFC", "#0B0F19", 4.5),
        ("Midnight: Secondary Text on Dark Card", "#CBD5E1", "#151E2E", 4.5),
        ("Midnight: Mint Accent on Dark Card", "#10B981", "#151E2E", 3.0),
        ("Midnight: Card Headings on Dark Card", "#FFFFFF", "#151E2E", 4.5),

        # Theme: High-Contrast Daylight (High Contrast)
        ("Daylight: Solid Black Text on White", "#000000", "#FFFFFF", 4.5),
        ("Daylight: Navy Heading on White", "#0A192F", "#FFFFFF", 4.5),
        ("Daylight: Dark Amber on White", "#854D0E", "#FFFFFF", 4.5),
        ("Daylight: Card Text on Pure White", "#000000", "#FFFFFF", 4.5)
    ]

    all_passed = True
    print("=" * 65)
    print("WCAG 2.1 THEME CONTRAST RATIO AUDIT")
    print("=" * 65)
    for name, fg, bg, threshold in checks:
        ratio = calculate_contrast_ratio(fg, bg)
        status = "PASS" if ratio >= threshold else "FAIL"
        if status == "FAIL":
            all_passed = False
        print(f"[{status}] {name:40s}: {ratio:5.2f}:1 (Target: >= {threshold:.1f}:1)")

    print("=" * 65)
    if all_passed:
        print("ALL CONTRAST CHECKS PASSED WCAG AA REQUIREMENTS!")
    else:
        print("SOME CONTRAST CHECKS FAILED!")
    return all_passed

if __name__ == "__main__":
    import sys
    success = check_all_themes()
    sys.exit(0 if success else 1)
