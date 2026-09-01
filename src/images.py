"""シルエットと円形カラー表示の画像処理。"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from data.kinoko_data import Highlight, KinokoDataError

SILHOUETTE_COLOR = (28, 25, 24, 255)


def create_quiz_image(
    source: str | Path | Image.Image,
    highlight: Highlight,
) -> Image.Image:
    """カラー画像から、指定した円内だけがカラーのシルエットを作る。"""

    if not highlight.is_positioned:
        raise KinokoDataError("highlight position must be set before creating quiz image")

    if isinstance(source, Image.Image):
        color_image = source.convert("RGBA")
    else:
        with Image.open(source) as opened:
            color_image = opened.convert("RGBA")

    width, height = color_image.size
    if width <= 0 or height <= 0:
        raise ValueError("source image must have a positive size")

    silhouette = Image.new("RGBA", color_image.size, SILHOUETTE_COLOR)
    silhouette.putalpha(color_image.getchannel("A"))

    scale = 4
    mask = Image.new("L", (width * scale, height * scale), 0)
    draw = ImageDraw.Draw(mask)
    center_x = highlight.x * width * scale
    center_y = highlight.y * height * scale
    radius = highlight.radius * min(width, height) * scale
    draw.ellipse(
        (
            center_x - radius,
            center_y - radius,
            center_x + radius,
            center_y + radius,
        ),
        fill=255,
    )
    mask = mask.resize(color_image.size, Image.Resampling.LANCZOS)

    result = Image.composite(color_image, silhouette, mask)
    result.putalpha(color_image.getchannel("A"))
    return result


def save_quiz_image(
    source: str | Path | Image.Image,
    highlight: Highlight,
    destination: str | Path,
) -> Path:
    """クイズ画像をPNGで保存し、保存先を返す。"""

    output_path = Path(destination)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    create_quiz_image(source, highlight).save(output_path, format="PNG", optimize=True)
    return output_path
