#!/usr/bin/env python3
"""README screenshots. Example.edu accounts only."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = Path(__file__).resolve().parent
ICON = Path(__file__).resolve().parent.parent / "icon.png"
FONT = "/System/Library/Fonts/SFNS.ttf"
SCALE = 2

BG = (236, 236, 238, 255)
PANEL = (28, 28, 30, 255)
LINE = (58, 58, 62, 255)
SELECT = (10, 132, 255, 255)
TITLE = (245, 245, 247, 255)
SUB = (174, 174, 178, 255)
FOOT = (142, 142, 147, 255)
QUERY = (255, 255, 255, 255)


def font(size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(FONT, size * SCALE)
    except OSError:
        return ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", size * SCALE)


def load_icon(size: int) -> Image.Image:
    icon = Image.open(ICON).convert("RGBA")
    return icon.resize((size, size), Image.Resampling.LANCZOS)


def draw_window(rows, query: str, selected: int, footer: str, name: str) -> None:
    s = SCALE
    pad = 56 * s
    width = 720 * s
    row_h = 58 * s
    header = 62 * s
    footer_h = 40 * s
    height = header + row_h * len(rows) + footer_h + pad * 2
    canvas = Image.new("RGBA", (width + pad * 2, height), BG)
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    panel = (pad, pad, pad + width, pad + header + row_h * len(rows) + footer_h)
    sd.rounded_rectangle(
        (panel[0] + 6, panel[1] + 10, panel[2] + 6, panel[3] + 14),
        radius=16 * s,
        fill=(0, 0, 0, 55),
    )
    canvas = Image.alpha_composite(canvas, shadow.filter(ImageFilter.GaussianBlur(18)))
    d = ImageDraw.Draw(canvas)
    d.rounded_rectangle(panel, radius=16 * s, fill=PANEL)
    d.text((pad + 24 * s, pad + 16 * s), query, font=font(22), fill=QUERY)
    yline = pad + header - 4 * s
    d.line([(pad + 16 * s, yline), (pad + width - 16 * s, yline)], fill=LINE, width=s)
    icon = load_icon(36 * s)
    for i, (title, sub) in enumerate(rows):
        y = pad + header + i * row_h
        if i == selected:
            d.rounded_rectangle(
                (pad + 10 * s, y + 5 * s, pad + width - 10 * s, y + row_h - 5 * s),
                radius=8 * s,
                fill=SELECT,
            )
            tfill, sfill = (255, 255, 255, 255), (220, 235, 255, 255)
        else:
            tfill, sfill = TITLE, SUB
        ix, iy = pad + 22 * s, y + (row_h - 36 * s) // 2
        canvas.paste(icon, (ix, iy), icon)
        d = ImageDraw.Draw(canvas)
        d.text((pad + 70 * s, y + 10 * s), title, font=font(17), fill=tfill)
        d.text((pad + 70 * s, y + 32 * s), sub, font=font(13), fill=sfill)
    fy = pad + header + row_h * len(rows)
    d.text((pad + 24 * s, fy + 10 * s), footer, font=font(12), fill=FOOT)
    canvas.convert("RGB").save(OUT / name, "PNG", optimize=True)


def main() -> int:
    draw_window(
        [
            ("jdoe@example.edu", "arizona.edu"),
            ("guest@example.edu", "WebAuth"),
            ("backup@example.edu", "webauth.arizona.edu"),
        ],
        "pw arizona",
        0,
        "return  Fill login      cmd  Password      opt  OTP      ctrl  User name",
        "search.png",
    )
    draw_window(
        [
            ("jdoe@example.edu", "arizona.edu  ·  current tab"),
            ("guest@example.edu", "arizona.edu  ·  current tab"),
        ],
        "pw",
        0,
        "Suggested from the front browser tab",
        "current-tab.png",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
