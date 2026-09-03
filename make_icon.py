#!/usr/bin/env python3
"""Write a 256x256 workflow icon. No third-party image libraries."""

from __future__ import annotations

import struct
import zlib
from pathlib import Path

SIZE = 256


def _chunk(tag: bytes, data: bytes) -> bytes:
    crc = zlib.crc32(tag + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)


def write_png(path: Path, pixels: bytearray, width: int, height: int) -> None:
    raw = bytearray()
    row_bytes = width * 4
    for y in range(height):
        raw.append(0)
        raw.extend(pixels[y * row_bytes : (y + 1) * row_bytes])
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    png = (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + _chunk(b"IEND", b"")
    )
    path.write_bytes(png)


def fill_rect(
    pixels: bytearray, x0: int, y0: int, x1: int, y1: int, color: tuple[int, int, int, int]
) -> None:
    r, g, b, a = color
    for y in range(max(0, y0), min(SIZE, y1)):
        row = y * SIZE * 4
        for x in range(max(0, x0), min(SIZE, x1)):
            i = row + x * 4
            pixels[i : i + 4] = bytes((r, g, b, a))


def fill_circle(
    pixels: bytearray, cx: int, cy: int, radius: int, color: tuple[int, int, int, int]
) -> None:
    r, g, b, a = color
    rr = radius * radius
    for y in range(max(0, cy - radius), min(SIZE, cy + radius + 1)):
        dy = y - cy
        row = y * SIZE * 4
        for x in range(max(0, cx - radius), min(SIZE, cx + radius + 1)):
            dx = x - cx
            if dx * dx + dy * dy <= rr:
                i = row + x * 4
                pixels[i : i + 4] = bytes((r, g, b, a))


def rounded_rect(
    pixels: bytearray,
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    radius: int,
    color: tuple[int, int, int, int],
) -> None:
    fill_rect(pixels, x0 + radius, y0, x1 - radius, y1, color)
    fill_rect(pixels, x0, y0 + radius, x1, y1 - radius, color)
    fill_circle(pixels, x0 + radius, y0 + radius, radius, color)
    fill_circle(pixels, x1 - radius - 1, y0 + radius, radius, color)
    fill_circle(pixels, x0 + radius, y1 - radius - 1, radius, color)
    fill_circle(pixels, x1 - radius - 1, y1 - radius - 1, radius, color)


def main() -> int:
    pixels = bytearray(SIZE * SIZE * 4)
    navy = (18, 42, 92, 255)
    white = (245, 248, 255, 255)
    rounded_rect(pixels, 16, 16, 240, 240, 48, navy)
    # lock body
    fill_rect(pixels, 88, 124, 168, 196, white)
    # lock shackle
    fill_rect(pixels, 100, 84, 116, 128, white)
    fill_rect(pixels, 140, 84, 156, 128, white)
    fill_rect(pixels, 100, 76, 156, 96, white)
    fill_rect(pixels, 116, 88, 140, 108, navy)
    # keyhole
    fill_circle(pixels, 128, 150, 10, navy)
    fill_rect(pixels, 124, 150, 132, 178, navy)
    write_png(Path(__file__).resolve().parent / "icon.png", pixels, SIZE, SIZE)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
