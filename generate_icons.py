#!/usr/bin/env python3
"""
Generate PWA icons (maskable-safe) + Apple touch icons from a source logo.

Usage:
  python tools/generate_icons.py "path/to/logo.png" --theme "#4CAF50" --out icons --padding 0.12
"""
from pathlib import Path
from PIL import Image
import argparse
import re

def parse_hex_color(value: str):
    m = re.fullmatch(r"#?([0-9a-fA-F]{6})", value.strip())
    if not m:
        raise argparse.ArgumentTypeError("Theme color must be a hex like #4CAF50")
    hex6 = m.group(1)
    r = int(hex6[0:2], 16)
    g = int(hex6[2:4], 16)
    b = int(hex6[4:6], 16)
    return (r, g, b, 255)

def make_icon(base_img: Image.Image, size: int, padding_ratio: float, solid_bg=False, theme=(76,175,80,255)):
    bg = Image.new('RGBA', (size, size), theme if solid_bg else (0, 0, 0, 0))
    content = int(size * (1 - 2 * padding_ratio))
    w, h = base_img.size
    scale = min(content / w, content / h)
    new_w = max(1, int(w * scale))
    new_h = max(1, int(h * scale))
    resized = base_img.resize((new_w, new_h), Image.LANCZOS)
    x = (size - new_w) // 2
    y = (size - new_h) // 2
    bg.alpha_composite(resized, (x, y))
    return bg

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("logo", help="Path to your logo (PNG with transparency preferred)")
    ap.add_argument("--out", default="icons", help="Output directory (default: icons)")
    ap.add_argument("--padding", type=float, default=0.12, help="Padding ratio (default: 0.12)")
    ap.add_argument("--theme", type=parse_hex_color, default="#4CAF50", help="Theme hex color for solid backgrounds")
    args = ap.parse_args()

    src = Path(args.logo)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    img = Image.open(src).convert('RGBA')

    # Auto-crop to non-transparent bounds if alpha channel exists
    alpha = img.split()[-1] if img.mode.endswith('A') else None
    bbox = alpha.getbbox() if alpha is not None else None
    logo = img.crop(bbox) if bbox else img

    sizes = [72, 96, 128, 144, 152, 167, 180, 192, 256, 384, 512]
    # Transparent (maskable) icons
    for s in sizes:
        make_icon(logo, s, args.padding, solid_bg=False).save(out_dir / f"icon-{s}.png", "PNG")
    # Solid variants (useful for some launchers/walls)
    for s in sizes:
        make_icon(logo, s, args.padding, solid_bg=True, theme=args.theme).save(out_dir / f"icon-{s}-solid.png", "PNG")
    # Apple touch icons (solid recommended)
    for s in [120, 152, 180]:
        make_icon(logo, s, args.padding, solid_bg=True, theme=args.theme).save(out_dir / f"apple-touch-icon-{s}.png", "PNG")

    print(f"✔ Icons written to: {out_dir.resolve()}")
    print("  - icon-192.png, icon-512.png (maskable) referenced by manifest.json")
    print("  - apple-touch-icon-180.png referenced by index.html")

if __name__ == "__main__":
    main()
