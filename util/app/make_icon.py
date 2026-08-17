#!/usr/bin/env python3
"""Generate Kokopelli's dot-matrix macOS icon using Pillow and iconutil."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFilter


CANVAS = 1024
GLYPHS = {
    "K": (
        "10001",
        "10010",
        "10100",
        "11000",
        "10100",
        "10010",
        "10001",
    ),
    "O": (
        "01110",
        "10001",
        "10001",
        "10001",
        "10001",
        "10001",
        "01110",
    ),
}


def _vertical_gradient(size: int, top: tuple[int, ...], bottom: tuple[int, ...]) -> Image.Image:
    image = Image.new("RGBA", (size, size))
    pixels = image.load()
    for y in range(size):
        ratio = y / (size - 1)
        color = tuple(round(a + (b - a) * ratio) for a, b in zip(top, bottom))
        for x in range(size):
            pixels[x, y] = color
    return image


def render_master() -> Image.Image:
    image = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))

    shadow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle((84, 78, 940, 934), radius=190, fill=(0, 18, 22, 185))
    image.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(34)))

    mask = Image.new("L", image.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((70, 54, 954, 938), radius=205, fill=255)
    face = _vertical_gradient(CANVAS, (7, 64, 77, 255), (0, 38, 48, 255))
    face.putalpha(mask)
    image.alpha_composite(face)

    rim = ImageDraw.Draw(image)
    rim.rounded_rectangle((70, 54, 954, 938), radius=205, outline=(42, 161, 152, 210), width=18)
    rim.arc((102, 86, 922, 906), 202, 338, fill=(145, 204, 190, 105), width=8)

    pitch = 62
    glyph_gap = 54
    dot_radius = 20
    width = 10 * pitch + glyph_gap
    height = 7 * pitch
    left = (CANVAS - width) // 2 + dot_radius
    top = (CANVAS - height) // 2 + dot_radius

    glow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    cursor = left
    for character in "KO":
        for row, bits in enumerate(GLYPHS[character]):
            for column, bit in enumerate(bits):
                if bit == "1":
                    x = cursor + column * pitch
                    y = top + row * pitch
                    glow_draw.ellipse((x - 30, y - 30, x + 30, y + 30), fill=(42, 161, 152, 185))
        cursor += 5 * pitch + glyph_gap
    image.alpha_composite(glow.filter(ImageFilter.GaussianBlur(15)))

    dots = ImageDraw.Draw(image)
    cursor = left
    for character in "KO":
        for row, bits in enumerate(GLYPHS[character]):
            for column, bit in enumerate(bits):
                if bit == "1":
                    x = cursor + column * pitch
                    y = top + row * pitch
                    dots.ellipse(
                        (x - dot_radius, y - dot_radius, x + dot_radius, y + dot_radius),
                        fill=(253, 246, 227, 255),
                    )
        cursor += 5 * pitch + glyph_gap
    return image


def main(argv: list[str]) -> int:
    output = Path(argv[1] if len(argv) > 1 else Path(__file__).with_name("ko.icns"))
    output.parent.mkdir(parents=True, exist_ok=True)
    master = render_master()
    entries = {
        "icon_16x16.png": 16,
        "icon_16x16@2x.png": 32,
        "icon_32x32.png": 32,
        "icon_32x32@2x.png": 64,
        "icon_128x128.png": 128,
        "icon_128x128@2x.png": 256,
        "icon_256x256.png": 256,
        "icon_256x256@2x.png": 512,
        "icon_512x512.png": 512,
        "icon_512x512@2x.png": 1024,
    }
    with tempfile.TemporaryDirectory(prefix="kokopelli-icon-") as temporary:
        iconset = Path(temporary) / "Kokopelli.iconset"
        iconset.mkdir()
        for filename, size in entries.items():
            master.resize((size, size), Image.Resampling.LANCZOS).save(iconset / filename)
        subprocess.run(
            ["iconutil", "--convert", "icns", "--output", str(output), str(iconset)],
            check=True,
        )
    print(f"Generated {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
