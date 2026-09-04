#!/usr/bin/env python3
"""Workflow icon: rounded navy tile with a lock."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

SIZE = 256
OUT = Path(__file__).resolve().parent / "icon.png"


def main() -> int:
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((8, 8, 248, 248), radius=56, fill=(20, 48, 110, 255))
    white = (245, 248, 255, 255)
    navy = (20, 48, 110, 255)
    d.arc((84, 46, 172, 134), 180, 0, fill=white, width=18)
    d.rectangle((84, 108, 102, 128), fill=white)
    d.rectangle((154, 108, 172, 128), fill=white)
    d.rounded_rectangle((74, 112, 182, 208), radius=20, fill=white)
    d.ellipse((112, 138, 144, 170), fill=navy)
    d.polygon([(122, 158), (134, 158), (140, 192), (116, 192)], fill=navy)
    # slight inner shadow on the tile edge
    shadow = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((8, 8, 248, 248), radius=56, outline=(0, 0, 0, 50), width=3)
    img = Image.alpha_composite(img, shadow.filter(ImageFilter.GaussianBlur(1)))
    img.save(OUT, "PNG")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
