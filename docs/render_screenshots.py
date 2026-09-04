#!/usr/bin/env python3
"""Draw README screenshots. Fake example.edu accounts only."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter

OUT = Path(__file__).resolve().parent
FONT = "/System/Library/Fonts/SFNS.ttf"
FONT_I = "/System/Library/Fonts/SFNSItalic.ttf"
SCALE = 2


def font(size: int, italic: bool = False) -> ImageFont.FreeTypeFont:
    path = FONT_I if italic else FONT
    try:
        return ImageFont.truetype(path, size * SCALE)
    except OSError:
        return ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", size * SCALE)


def rounded(draw: ImageDraw.ImageDraw, box, radius, fill):
    draw.rounded_rectangle(box, radius=radius * SCALE, fill=fill)


def draw_window(rows, query: str, selected: int, footer: str, name: str) -> None:
    pad = 48 * SCALE
    width = 740 * SCALE
    row_h = 56 * SCALE
    header = 64 * SCALE
    footer_h = 36 * SCALE
    height = header + row_h * len(rows) + footer_h + pad * 2
    img = Image.new("RGBA", (width + pad * 2, height), (232, 232, 234, 255))
    d = ImageDraw.Draw(img)
    panel = (pad, pad, pad + width, pad + header + row_h * len(rows) + footer_h)
    # shadow
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle(
        (panel[0] + 8, panel[1] + 12, panel[2] + 8, panel[3] + 12),
        radius=18 * SCALE,
        fill=(0, 0, 0, 40),
    )
    img = Image.alpha_composite(img, shadow.filter(ImageFilter.GaussianBlur(12)))
    d = ImageDraw.Draw(img)
    rounded(d, panel, 18, (36, 36, 38, 255))
    # query
    qfont = font(22)
    d.text((pad + 28 * SCALE, pad + 18 * SCALE), query, font=qfont, fill=(245, 245, 247, 255))
    d.line(
        [(pad + 20 * SCALE, pad + header - 2), (pad + width - 20 * SCALE, pad + header - 2)],
        fill=(70, 70, 74, 255),
        width=SCALE,
    )
    title_f = font(17)
    sub_f = font(13)
    for i, (title, sub) in enumerate(rows):
        y = pad + header + i * row_h
        if i == selected:
            d.rectangle(
                (pad + 8 * SCALE, y + 4 * SCALE, pad + width - 8 * SCALE, y + row_h - 4 * SCALE),
                fill=(52, 120, 246, 255),
            )
            tfill, sfill = (255, 255, 255, 255), (220, 230, 255, 255)
        else:
            tfill, sfill = (236, 236, 238, 255), (160, 160, 165, 255)
        cx, cy = pad + 36 * SCALE, y + row_h // 2
        r = 13 * SCALE
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=tfill)
        d.text((pad + 64 * SCALE, y + 8 * SCALE), title, font=title_f, fill=tfill)
        d.text((pad + 64 * SCALE, y + 30 * SCALE), sub, font=sub_f, fill=sfill)
    fy = pad + header + row_h * len(rows)
    d.text((pad + 24 * SCALE, fy + 8 * SCALE), footer, font=font(12), fill=(150, 150, 155, 255))
    img = img.convert("RGB")
    img.save(OUT / name, "PNG", optimize=True)


def main() -> int:
    draw_window(
        [
            ("jdoe@example.edu", "arizona.edu"),
            ("guest@example.edu", "WebAuth"),
            ("backup@example.edu", "webauth.arizona.edu"),
        ],
        "pw arizona",
        0,
        "↩ Fill login    ⌘ Copy password    ⌥ OTP    ⌃ User name",
        "search.png",
    )
    draw_window(
        [
            ("jdoe@example.edu", "arizona.edu  ·  current tab"),
            ("guest@example.edu", "arizona.edu  ·  current tab"),
        ],
        "pw",
        0,
        "Suggested from the frontmost browser tab",
        "current-tab.png",
    )
    print(OUT / "search.png")
    print(OUT / "current-tab.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
