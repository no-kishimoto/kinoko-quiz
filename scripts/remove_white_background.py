"""白っぽい背景を透明化して、図鑑・クイズ用の素材を作り直す。"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data.kinoko_data import Highlight, load_kinoko
from data.subject_data import load_ready_subject_items
from src.images import save_quiz_image
from src.paths import (
    KONCHUU_DATA_PATH,
    KONCHUU_QUIZ_IMAGE_DIR,
    KONCHUU_ZUKAN_IMAGE_DIR,
    DATA_PATH,
    QUIZ_IMAGE_DIR,
    SHOKUBUTSU_DATA_PATH,
    SHOKUBUTSU_QUIZ_IMAGE_DIR,
    SHOKUBUTSU_ZUKAN_IMAGE_DIR,
    ZUKAN_IMAGE_DIR,
)

SHOKUBUTSU_HIGHLIGHTS = {
    "sakura": Highlight("はなびら", 0.37, 0.31, 0.16),
    "tanpopo": Highlight("はなと わたげ", 0.5, 0.25, 0.34),
    "himawari": Highlight("たねの まんなか", 0.5, 0.31, 0.15),
    "asagao": Highlight("ラッパの はな", 0.42, 0.32, 0.17),
    "chuurippu": Highlight("カップの はな", 0.48, 0.3, 0.17),
    "bara": Highlight("はなびらの うず", 0.48, 0.31, 0.16),
    "saracenia": Highlight("つつの くち", 0.5, 0.42, 0.17),
    "shirotsumekusa": Highlight("しろい まるい はな", 0.43, 0.28, 0.16),
    "nekopanjya": Highlight("ふわふわの はな", 0.48, 0.35, 0.17),
    "donguri": Highlight("ぼうし", 0.46, 0.35, 0.15),
    "ninjin": Highlight("オレンジの ねっこ", 0.5, 0.57, 0.17),
    "tomato": Highlight("あかい みと へた", 0.48, 0.42, 0.17),
    "kyuuri": Highlight("いぼいぼの み", 0.5, 0.5, 0.17),
    "kabocha": Highlight("しまもよう", 0.5, 0.48, 0.17),
    "jagaimo": Highlight("ちゃいろい かわ", 0.48, 0.5, 0.16),
    "tamanegi": Highlight("まるい たま", 0.5, 0.47, 0.16),
    "daikon": Highlight("しろい ねっこ", 0.5, 0.58, 0.17),
    "piiman": Highlight("みどりの みと へた", 0.48, 0.43, 0.16),
    "toumorokoshi": Highlight("きいろい つぶ", 0.48, 0.47, 0.17),
    "edamame": Highlight("まめの さや", 0.5, 0.49, 0.17),
    "okura": Highlight("ほしがたの きりくち", 0.48, 0.44, 0.16),
    "ringo": Highlight("あかい みと へた", 0.48, 0.38, 0.16),
    "mikan": Highlight("オレンジの かわ", 0.48, 0.44, 0.16),
    "banana": Highlight("きいろい み", 0.5, 0.48, 0.18),
    "ichigo": Highlight("つぶつぶの み", 0.48, 0.43, 0.16),
    "budou": Highlight("むらさきの つぶ", 0.48, 0.46, 0.17),
    "momo": Highlight("ピンクの かわ", 0.48, 0.43, 0.16),
    "nashi": Highlight("ちゃいろい かわ", 0.48, 0.43, 0.16),
    "suika": Highlight("みどりの しま", 0.48, 0.44, 0.17),
    "meron": Highlight("あみめもよう", 0.48, 0.44, 0.17),
    "kaki": Highlight("オレンジの みと へた", 0.48, 0.4, 0.16),
    "haetorigusa": Highlight("とじる は", 0.49, 0.42, 0.17),
    "utsubokazura": Highlight("つぼの ぶぶん", 0.5, 0.73, 0.19),
    "mousengoke": Highlight("ねばねばの け", 0.5, 0.43, 0.17),
    "saboten": Highlight("とげ", 0.49, 0.36, 0.16),
    "matsu": Highlight("まつぼっくり", 0.48, 0.57, 0.16),
    "ichou": Highlight("うちわの は", 0.45, 0.38, 0.17),
    "momiji": Highlight("てのひらの は", 0.48, 0.37, 0.17),
    "take": Highlight("ふし", 0.5, 0.46, 0.16),
    "blueberry": Highlight("あおい み", 0.49, 0.42, 0.16),
}
KONCHUU_HIGHLIGHTS = {
    "kabutomushi": Highlight("おおきな つの", 0.5, 0.27, 0.16),
    "hercules_ookabuto": Highlight("ながい つの", 0.5, 0.25, 0.18),
    "caucasus_ookabuto": Highlight("3ぼんの つの", 0.5, 0.27, 0.18),
    "ookuwagata": Highlight("ふとい おおあご", 0.5, 0.28, 0.17),
    "nokogirikuwagata": Highlight("のこぎりの おおあご", 0.5, 0.27, 0.18),
    "miyamakuwagata": Highlight("ひろがった おおあご", 0.5, 0.27, 0.18),
    "kokuwagata": Highlight("ちいさな おおあご", 0.5, 0.3, 0.16),
    "ogon_onikuwagata": Highlight("きんいろの おおあご", 0.5, 0.27, 0.18),
    "kamikirimushi": Highlight("ながい しょっかく", 0.52, 0.28, 0.18),
    "kamakiri": Highlight("かまの まえあし", 0.46, 0.4, 0.18),
    "oniyanma": Highlight("みどりの め", 0.48, 0.34, 0.16),
    "agehachou": Highlight("きいろと くろの はね", 0.48, 0.43, 0.19),
    "monshirochou": Highlight("しろい はねの もん", 0.48, 0.43, 0.18),
    "aburazemi": Highlight("すきとおる はね", 0.5, 0.43, 0.19),
    "ari": Highlight("6ほんの あし", 0.48, 0.49, 0.16),
    "mitsubachi": Highlight("しまもようの おなか", 0.5, 0.48, 0.16),
    "tentoumushi": Highlight("あかい はねの くろいてん", 0.48, 0.43, 0.16),
    "batta": Highlight("おおきな うしろあし", 0.5, 0.52, 0.18),
    "koorogi": Highlight("ながい しょっかく", 0.5, 0.32, 0.17),
    "suzumushi": Highlight("はねの もよう", 0.5, 0.45, 0.17),
    "hotaru": Highlight("ひかる おなか", 0.5, 0.55, 0.16),
    "kamemushi": Highlight("たての かたち", 0.5, 0.45, 0.16),
    "suzumebachi": Highlight("きいろと くろの しま", 0.5, 0.46, 0.17),
    "kanabun": Highlight("みどりに ひかる はね", 0.49, 0.43, 0.16),
    "hae": Highlight("あかい め", 0.48, 0.36, 0.15),
    "ka": Highlight("ながい あしと はり", 0.5, 0.45, 0.18),
    "nijiirokuwagata": Highlight("にじいろの からだ", 0.5, 0.43, 0.17),
    "girafanokogirikuwagata": Highlight("ながい おおあご", 0.5, 0.27, 0.19),
    "goliathus_goliatus": Highlight("しろと くろの もよう", 0.5, 0.43, 0.18),
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

    temporary_path = path.with_suffix(".tmp.png")
    image.save(temporary_path, format="PNG", optimize=True)
    os.replace(temporary_path, path)


def rebuild_subject_assets(
    data_path: Path,
    zukan_dir: Path,
    quiz_dir: Path,
    highlights: dict[str, Highlight],
) -> None:
    for item in load_ready_subject_items(data_path):
        source = zukan_dir / item.image_filename
        make_background_transparent(source)
        try:
            highlight = highlights[item.key]
        except KeyError as exc:
            raise ValueError(f"missing highlight for {item.key}") from exc
        destination = quiz_dir / item.image_filename
        temporary_path = destination.with_suffix(".tmp.png")
        save_quiz_image(source, highlight, temporary_path)
        os.replace(temporary_path, destination)


def rebuild_kinoko_assets() -> None:
    """きのこもデータごとの指定位置でクイズ画像を作り直す。"""

    for item in load_kinoko(DATA_PATH):
        destination = QUIZ_IMAGE_DIR / item.image_filename
        temporary_path = destination.with_suffix(".tmp.png")
        save_quiz_image(ZUKAN_IMAGE_DIR / item.image_filename, item.highlight, temporary_path)
        os.replace(temporary_path, destination)


if __name__ == "__main__":
    rebuild_subject_assets(
        SHOKUBUTSU_DATA_PATH,
        SHOKUBUTSU_ZUKAN_IMAGE_DIR,
        SHOKUBUTSU_QUIZ_IMAGE_DIR,
        SHOKUBUTSU_HIGHLIGHTS,
    )
    rebuild_subject_assets(KONCHUU_DATA_PATH, KONCHUU_ZUKAN_IMAGE_DIR, KONCHUU_QUIZ_IMAGE_DIR, KONCHUU_HIGHLIGHTS)
    rebuild_kinoko_assets()
