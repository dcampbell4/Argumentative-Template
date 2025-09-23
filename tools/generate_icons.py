#!/usr/bin/env python3
"""
Generate PWA icons (maskable-safe) + Apple touch icons from a URL or local file.

Examples:
  # From URL (recommended in your case)
  python tools/generate_icons.py --logo-url "https://i.postimg.cc/gcCdtgqs/Elegant-Emblem-Logo-Design.png" --out "./icons" --theme "#4CAF50" -v

  # From local file
  python tools/generate_icons.py --logo "assets/logo.png" --out "./icons" -v
"""
from pathlib import Path
from PIL import Image
import argparse, re, sys, tempfile, urllib.request

def parse_hex_color(value: str):
    m = re.fullmatch(r"#?([0-9a-fA-F]{6})", value.strip())
    if not m:
        raise argparse.ArgumentTypeError("Theme color must be a hex like #4CAF50")
    hex6 = m.group(1)
    return (int(hex6[0:2],16), int(hex6[2:4],16), int(hex6[4:6],16), 255)

def make_icon(base_img: Image.Image, size: int, padding_ratio: float, solid_bg=False, theme=(76,175,80,255)):
    bg = Image.new('RGBA', (size, size), theme if solid_bg else (0,0,0,0))
    content = int(size * (1 - 2*padding_ratio))
    w, h = base_img.size
    scale = min(content / w, content / h)
    new_w, new_h = max(1, int(w*scale)), max(1, int(h*scale))
    resized = base_img.resize((new_w, new_h), Image.LANCZOS)
    x = (size - new_w) // 2
    y = (size - new_h) // 2
    bg.alpha_composite(resized, (x, y))
    return bg

def load_logo(path_or_url: str) -> Image.Image:
    # If it looks like a URL, download it to a temp file
    if path_or_url.lower().startswith(("http://", "https://")):
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        tmp.close()  # close handle for Windows
        print(f"⬇️  Downloading logo from URL:\n   {path_or_url}")
        urllib.request.urlretrieve(path_or_url, tmp.name)
        logo_path = Path(tmp.name)
    else:
        logo_path = Path(path_or_url).expanduser().resolve()
        if not logo_path.exists():
            print(f"✖ Local logo not found: {logo_path}")
            sys.exit(1)
    print(f"✔ Using logo file: {logo_path}")
    return Image.open(logo_path).convert("RGBA")

def main():
    ap = argparse.ArgumentParser()
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--logo", help="Path to local logo file (PNG preferred)")
    group.add_argument("--logo-url", help="HTTPS URL of the logo image (PNG preferred)")
    ap.add_argument("--out", default="icons", help="Output directory (default: icons)")
    ap.add_argument("--padding", type=float, default=0.12, help="Padding ratio (default: 0.12)")
    ap.add_argument("--theme", type=parse_hex_color, default="#4CAF50", help="Theme color for solid variants")
    ap.add_argument("--no-solid", action="store_true", help="Skip solid background icon variants")
    ap.add_argument("--verbose", "-v", action="store_true")
    args = ap.parse_args()

    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"Working directory: {Path.cwd().resolve()}")
    print(f"Output directory:  {out_dir}")

    try:
        img = load_logo(args.logo_url or args.logo)
    except Exception as e:
        print(f"✖ Failed to load logo: {e}")
        print("  Tip: Ensure the URL returns an image (not an HTML page) and Pillow is installed.")
        sys.exit(1)

    # Auto-crop to non-transparent bounds if present
    alpha = img.split()[-1] if img.mode.endswith('A') else None
    bbox = alpha.getbbox() if alpha is not None else None
    logo = img.crop(bbox) if bbox else img
    if args.verbose:
        print(f"Alpha channel: {'yes' if alpha else 'no'}; Cropped: {'yes' if bbox else 'no'}")

    THEME = args.theme
    PADDING = args.padding
    sizes_all = [72, 96, 128, 144, 152, 167, 180, 192, 256, 384, 512]

    generated = []

    # Transparent (maskable) icons
    for s in sizes_all:
        path = out_dir / f"icon-{s}.png"
        make_icon(logo, s, PADDING, solid_bg=False).save(path, "PNG")
        generated.append(path)
        if args.verbose: print(f"✔ Wrote {path}")

    # Solid variants (useful on some launchers)
    if not args.no-solid:
        for s in sizes_all:
            path = out_dir / f"icon-{s}-solid.png"
            make_icon(logo, s, PADDING, solid_bg=True, theme=THEME).save(path, "PNG")
            generated.append(path)
            if args.verbose: print(f"✔ Wrote {path}")

    # Apple touch icons (solid recommended)
    for s in [120, 152, 180]:
        path = out_dir / f"apple-touch-icon-{s}.png"
        make_icon(logo, s, PADDING, solid_bg=True, theme=THEME).save(path, "PNG")
        generated.append(path)
        if args.verbose: print(f"✔ Wrote {path}")

    print(f"\n✔ Done. Wrote {len(generated)} files into:\n  {out_dir}\n")
    print("Next steps:")
    print('  - Reference icons in manifest.json and index.html as shown below.')

if __name__ == "__main__":
    main()
