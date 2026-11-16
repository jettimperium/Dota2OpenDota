from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
ASSETS.mkdir(parents=True, exist_ok=True)

SIZE = 1024
OUTER = int(SIZE * 0.06)
RADIUS = int(SIZE * 0.245)


def lerp(a: int, b: int, t: float) -> int:
    return round(a + (b - a) * t)


def make_icon() -> Image.Image:
    image = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    mask = Image.new("L", (SIZE, SIZE), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle(
        (OUTER, OUTER, SIZE - OUTER, SIZE - OUTER),
        radius=RADIUS,
        fill=255,
    )

    gradient = Image.new("RGBA", (SIZE, SIZE))
    grad_draw = ImageDraw.Draw(gradient)
    for y in range(SIZE):
        t = y / SIZE
        top = (105, 237, 193)
        bottom = (20, 166, 118)
        grad_draw.line(
            [(0, y), (SIZE, y)],
            fill=(
                lerp(top[0], bottom[0], t),
                lerp(top[1], bottom[1], t),
                lerp(top[2], bottom[2], t),
                255,
            ),
        )
    image.paste(gradient, (0, 0), mask)

    # Тонкая тёмная рамка.
    draw.rounded_rectangle(
        (OUTER + 5, OUTER + 5, SIZE - OUTER - 5, SIZE - OUTER - 5),
        radius=RADIUS - 4,
        outline=(6, 25, 19, 130),
        width=8,
    )

    # Блик в верхнем левом углу.
    highlight = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    hd = ImageDraw.Draw(highlight)
    hd.ellipse(
        (int(SIZE * 0.08), int(SIZE * 0.04), int(SIZE * 0.78), int(SIZE * 0.6)),
        fill=(255, 255, 255, 34),
    )
    highlight.putalpha(Image.composite(highlight.getchannel("A"), Image.new("L", (SIZE, SIZE), 0), mask))
    image.alpha_composite(highlight)

    font_path = Path(r"C:\Windows\Fonts\bahnschrift.ttf")
    font = ImageFont.truetype(str(font_path), int(SIZE * 0.41))
    text = "D2"
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    text_w = right - left
    text_h = bottom - top
    text_x = (SIZE - text_w) / 2 - left
    text_y = SIZE * 0.36 - text_h / 2 - top
    draw.text((text_x, text_y), text, font=font, fill=(5, 24, 18, 255))

    # Пульс-линия снизу.
    line_y = int(SIZE * 0.67)
    points = [
        (int(SIZE * 0.27), line_y),
        (int(SIZE * 0.41), line_y),
        (int(SIZE * 0.475), int(SIZE * 0.60)),
        (int(SIZE * 0.55), int(SIZE * 0.76)),
        (int(SIZE * 0.62), line_y),
        (int(SIZE * 0.74), line_y),
    ]
    draw.line(points, fill=(5, 24, 18, 255), width=int(SIZE * 0.032), joint="curve")
    for point in (points[0], points[-1]):
        draw.ellipse(
            (
                point[0] - int(SIZE * 0.019),
                point[1] - int(SIZE * 0.019),
                point[0] + int(SIZE * 0.019),
                point[1] + int(SIZE * 0.019),
            ),
            fill=(5, 24, 18, 255),
        )

    return image


def main() -> None:
    image = make_icon()
    png_path = ASSETS / "app.png"
    ico_path = ASSETS / "app.ico"
    image.resize((512, 512), Image.Resampling.LANCZOS).save(png_path)
    image.save(
        ico_path,
        format="ICO",
        sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)],
    )
    print(f"Создано: {png_path}")
    print(f"Создано: {ico_path}")


if __name__ == "__main__":
    main()
