"""Generate packaging/vltool.ico from a simple programmatic design.

Run:
    python scripts/generate_icon.py

Overwrites packaging/vltool.ico on every run.
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = Path(__file__).resolve().parents[1]
ICON_PATH = REPO_ROOT / "packaging" / "vltool.ico"

BG_TOP = (91, 46, 178)
BG_BOTTOM = (30, 17, 74)
FG = (255, 255, 255)
ACCENT = (255, 194, 92)


def _draw_base(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    radius = size // 6
    for y in range(size):
        t = y / max(size - 1, 1)
        r = int(BG_TOP[0] + (BG_BOTTOM[0] - BG_TOP[0]) * t)
        g = int(BG_TOP[1] + (BG_BOTTOM[1] - BG_TOP[1]) * t)
        b = int(BG_TOP[2] + (BG_BOTTOM[2] - BG_TOP[2]) * t)
        draw.line([(0, y), (size, y)], fill=(r, g, b, 255))

    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size - 1, size - 1), radius=radius, fill=255)
    rounded = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    rounded.paste(img, (0, 0), mask)

    draw = ImageDraw.Draw(rounded)
    cx, cy = size / 2, size / 2
    tri_r = size * 0.22
    triangle = [
        (cx - tri_r * 0.55, cy - tri_r),
        (cx - tri_r * 0.55, cy + tri_r),
        (cx + tri_r * 0.9, cy),
    ]
    draw.polygon(triangle, fill=ACCENT)

    bar_w = size * 0.58
    bar_h = max(2, size // 32)
    bar_y = cy + tri_r + size * 0.12
    draw.rounded_rectangle(
        (cx - bar_w / 2, bar_y, cx + bar_w / 2, bar_y + bar_h),
        radius=bar_h // 2,
        fill=FG,
    )

    return rounded


def main() -> int:
    sizes = [16, 24, 32, 48, 64, 128, 256]
    frames = [_draw_base(s) for s in sizes]
    ICON_PATH.parent.mkdir(parents=True, exist_ok=True)
    frames[-1].save(
        ICON_PATH,
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=frames[:-1],
    )
    print(f"[icon] wrote {ICON_PATH} ({ICON_PATH.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
