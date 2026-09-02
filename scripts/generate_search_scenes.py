"""きのこ探し15問分の背景画像を作る。"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from src.search import SEARCH_QUESTIONS


BASE_PATH = ROOT / "assets" / "images" / "search" / "forest_base.png"
ZUKAN_DIR = ROOT / "assets" / "images" / "zukan"
OUTPUT_DIR = ROOT / "assets" / "images" / "search" / "questions"


def remove_blue_background(image: Image.Image) -> Image.Image:
    """図鑑絵の青い背景を透明にして、森の上へ重ねられるようにする。"""

    rgba = image.convert("RGBA")
    pixels = rgba.load()
    for y in range(rgba.height):
        for x in range(rgba.width):
            red, green, blue, alpha = pixels[x, y]
            if blue > 145 and green > 110 and red < 130 and blue > red + 40:
                pixels[x, y] = (red, green, blue, 0)
    return rgba


def make_scene(question_index: int) -> Image.Image:
    with Image.open(BASE_PATH) as opened:
        background = opened.convert("RGB")
    if question_index % 2:
        background = ImageOps.mirror(background)
    brightness = (0.90, 1.00, 1.08)[question_index % 3]
    background = ImageEnhance.Brightness(background).enhance(brightness).convert("RGBA")
    width, height = background.size
    for target_index, target in enumerate(SEARCH_QUESTIONS[question_index].targets):
        with Image.open(ZUKAN_DIR / f"{target.key}.png") as opened:
            sprite = remove_blue_background(opened)
        alpha_box = sprite.getbbox()
        if alpha_box is not None:
            sprite = sprite.crop(alpha_box)
        size = int(min(width, height) * (0.22 + target_index * 0.015))
        sprite.thumbnail((size, size), Image.Resampling.LANCZOS)
        center_x = int(target.x * width)
        bottom_y = int((target.y + target.radius * 0.55) * height)
        background.alpha_composite(sprite, (center_x - sprite.width // 2, bottom_y - sprite.height))
    return background.convert("RGB")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for index, question in enumerate(SEARCH_QUESTIONS):
        make_scene(index).save(OUTPUT_DIR / question.image_filename, "PNG", optimize=True)


if __name__ == "__main__":
    main()
