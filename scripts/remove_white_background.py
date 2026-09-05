"""白っぽい背景を透明化して、図鑑・クイズ用の素材を作り直す。"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data.kinoko_data import Highlight
from data.subject_data import load_ready_subject_items
from src.images import save_quiz_image
from src.paths import (
    KONCHUU_DATA_PATH,
    KONCHUU_QUIZ_IMAGE_DIR,
    KONCHUU_ZUKAN_IMAGE_DIR,
    SHOKUBUTSU_DATA_PATH,
    SHOKUBUTSU_QUIZ_IMAGE_DIR,
    SHOKUBUTSU_ZUKAN_IMAGE_DIR,
)

DEFAULT_HIGHLIGHT = Highlight("いろの ぶぶん", 0.5, 0.45, 0.14)
SHOKUBUTSU_HIGHLIGHTS = {
    # きいろい花と、しろいわた毛を一度に見せる。
    "tanpopo": Highlight("はなと わたげ", 0.5, 0.25, 0.34),
    # うつぼかずららしさが分かる、中央につり下がったつぼを見せる。
    "utsubokazura": Highlight("つぼの ぶぶん", 0.5, 0.73, 0.19),
}


def is_background(pixel: tuple[int, int, int, int]) -> bool:
    red, green, blue, alpha = pixel
    return alpha > 0 and min(red, green, blue) >= 220 and max(red, green, blue) - min(red, green, blue) <= 35


def make_background_transparent(path: Path) -> None:
    """端からつながる白っぽい領域だけを透明にする。"""

    with Image.open(path) as opened:
        image = opened.convert("RGBA")

    width, height = image.size
    pixels = image.load()
    edge_points = [
        *((x, 0) for x in range(width)),
        *((x, height - 1) for x in range(width)),
        *((0, y) for y in range(height)),
        *((width - 1, y) for y in range(height)),
    ]
    for point in edge_points:
        if is_background(pixels[point]):
            ImageDraw.floodfill(image, point, (0, 0, 0, 0), thresh=35)

    image.save(path, format="PNG", optimize=True)


def rebuild_subject_assets(
    data_path: Path,
    zukan_dir: Path,
    quiz_dir: Path,
    highlights: dict[str, Highlight] | None = None,
) -> None:
    for item in load_ready_subject_items(data_path):
        source = zukan_dir / item.image_filename
        make_background_transparent(source)
        highlight = (highlights or {}).get(item.key, DEFAULT_HIGHLIGHT)
        save_quiz_image(source, highlight, quiz_dir / item.image_filename)


if __name__ == "__main__":
    rebuild_subject_assets(
        SHOKUBUTSU_DATA_PATH,
        SHOKUBUTSU_ZUKAN_IMAGE_DIR,
        SHOKUBUTSU_QUIZ_IMAGE_DIR,
        SHOKUBUTSU_HIGHLIGHTS,
    )
    rebuild_subject_assets(KONCHUU_DATA_PATH, KONCHUU_ZUKAN_IMAGE_DIR, KONCHUU_QUIZ_IMAGE_DIR)
