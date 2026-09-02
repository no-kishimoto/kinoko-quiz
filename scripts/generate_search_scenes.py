"""現在のランダムきのこ探しの、確認用プレビューを15枚作る。"""

from __future__ import annotations

import random
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from data.kinoko_data import load_kinoko
from src.paths import DATA_PATH, SEARCH_BACKGROUND_DIR, ZUKAN_IMAGE_DIR
from src.search import create_search_session, render_scene


OUTPUT_DIR = ROOT / "assets" / "images" / "search" / "previews"


def main() -> None:
    """固定した乱数で、現在のルールに沿う15問の見本を作る。"""

    kinoko = load_kinoko(DATA_PATH)
    backgrounds = tuple(sorted(SEARCH_BACKGROUND_DIR.glob("*.png")))
    if len(backgrounds) < 3:
        raise RuntimeError("at least three search backgrounds are required")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for index in range(15):
        session = create_search_session(kinoko, backgrounds, random.Random(index))
        render_scene(session, ZUKAN_IMAGE_DIR).save(OUTPUT_DIR / f"preview_{index + 1:02d}.png")


if __name__ == "__main__":
    main()
