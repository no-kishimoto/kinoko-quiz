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
    "tanpopo": Highlight("きいろい はなと わたげ", 0.5, 0.29, 0.28),
    "himawari": Highlight("たねの まんなか", 0.5, 0.31, 0.15),
    "asagao": Highlight("ラッパの はな", 0.49, 0.18, 0.17),
    "chuurippu": Highlight("カップの はな", 0.5, 0.17, 0.17),
    "bara": Highlight("はなびらの うず", 0.48, 0.31, 0.16),
    "saracenia": Highlight("つつの くち", 0.51, 0.24, 0.18),
    "shirotsumekusa": Highlight("しろい まるい はな", 0.5, 0.2, 0.16),
    "nekopanjya": Highlight("ふわふわの はな", 0.49, 0.15, 0.14),
    "donguri": Highlight("みの ぼうし", 0.55, 0.64, 0.18),
    "ninjin": Highlight("オレンジの ねっこ", 0.5, 0.57, 0.17),
    "tomato": Highlight("あかい みと へた", 0.4, 0.48, 0.18),
    "kyuuri": Highlight("いぼいぼの み", 0.5, 0.5, 0.17),
    "kabocha": Highlight("みの しまもよう", 0.51, 0.7, 0.19),
    "jagaimo": Highlight("ちゃいろい いも", 0.5, 0.82, 0.17),
    "tamanegi": Highlight("まるい たま", 0.5, 0.69, 0.18),
    "daikon": Highlight("しろい ねっこ", 0.5, 0.67, 0.19),
    "piiman": Highlight("みどりの み", 0.63, 0.6, 0.18),
    "toumorokoshi": Highlight("きいろい つぶ", 0.56, 0.55, 0.17),
    "edamame": Highlight("まめの さや", 0.49, 0.59, 0.18),
    "okura": Highlight("みどりの ながい さや", 0.64, 0.65, 0.2),
    "ringo": Highlight("あかい みと へた", 0.48, 0.38, 0.16),
    "mikan": Highlight("オレンジの かわ", 0.61, 0.43, 0.16),
    "banana": Highlight("きいろい み", 0.64, 0.73, 0.17),
    "ichigo": Highlight("つぶつぶの みと へた", 0.3, 0.7, 0.17),
    "budou": Highlight("むらさきの つぶ", 0.53, 0.69, 0.2),
    "momo": Highlight("ピンクの かわ", 0.45, 0.52, 0.17),
    "nashi": Highlight("ちゃいろい み", 0.42, 0.73, 0.18),
    "suika": Highlight("みの しまもよう", 0.54, 0.7, 0.19),
    "meron": Highlight("みの あみめもよう", 0.52, 0.74, 0.19),
    "kaki": Highlight("オレンジの みと へた", 0.65, 0.36, 0.18),
    "haetorigusa": Highlight("とじる はの とげ", 0.69, 0.22, 0.18),
    "utsubokazura": Highlight("つぼの ぶぶん", 0.5, 0.73, 0.19),
    "mousengoke": Highlight("はの ねばねばの け", 0.4, 0.3, 0.18),
    "saboten": Highlight("からだの とげ", 0.41, 0.62, 0.17),
    "matsu": Highlight("まつぼっくり", 0.48, 0.57, 0.16),
    "ichou": Highlight("うちわの は", 0.32, 0.26, 0.16),
    "momiji": Highlight("てのひらの は", 0.4, 0.3, 0.16),
    "take": Highlight("ふし", 0.5, 0.46, 0.16),
    "blueberry": Highlight("あおい み", 0.49, 0.42, 0.16),
}
KONCHUU_HIGHLIGHTS = {
    "kabutomushi": Highlight("おおきな つの", 0.23, 0.3, 0.17),
    "hercules_ookabuto": Highlight("ながい 2ほんの つの", 0.37, 0.36, 0.25),
    "caucasus_ookabuto": Highlight("3ぼんの つの", 0.57, 0.29, 0.24),
    "ookuwagata": Highlight("ふとい おおあご", 0.4, 0.24, 0.21),
    "nokogirikuwagata": Highlight("のこぎりの おおあご", 0.36, 0.3, 0.24),
    "miyamakuwagata": Highlight("あたまの でっぱり", 0.43, 0.37, 0.16),
    "kokuwagata": Highlight("ちいさな おおあご", 0.22, 0.49, 0.17),
    "ogon_onikuwagata": Highlight("きんいろの おおあご", 0.5, 0.27, 0.18),
    "kamikirimushi": Highlight("ながい しょっかく", 0.53, 0.28, 0.27),
    "kamakiri": Highlight("かまの まえあし", 0.24, 0.42, 0.19),
    "oniyanma": Highlight("おおきな みどりの め", 0.5, 0.165, 0.075),
    "agehachou": Highlight("きいろと くろの はね", 0.24, 0.3, 0.2),
    "monshirochou": Highlight("しろい はねの くろい もん", 0.28, 0.32, 0.12),
    "aburazemi": Highlight("ちゃいろい はね", 0.66, 0.68, 0.18),
    "ari": Highlight("からだの 3つの ぶぶん", 0.52, 0.49, 0.27),
    "mitsubachi": Highlight("しまもようの おなか", 0.69, 0.61, 0.18),
    "tentoumushi": Highlight("あかい はねの くろいてん", 0.56, 0.34, 0.18),
    "batta": Highlight("おおきな うしろあし", 0.7, 0.4, 0.23),
    "koorogi": Highlight("おおきな うしろあし", 0.62, 0.35, 0.22),
    "suzumushi": Highlight("まるく ひろい はね", 0.58, 0.55, 0.18),
    "hotaru": Highlight("ひかる おしり", 0.65, 0.76, 0.16),
    "kamemushi": Highlight("たての かたち", 0.5, 0.54, 0.2),
    "suzumebachi": Highlight("おなかの きいろと くろの しま", 0.74, 0.58, 0.18),
    "kanabun": Highlight("みどりに ひかる はね", 0.49, 0.43, 0.16),
    "hae": Highlight("あかちゃいろの め", 0.26, 0.5, 0.11),
    "ka": Highlight("ながい あし", 0.4, 0.62, 0.26),
    "nijiirokuwagata": Highlight("にじいろの からだ", 0.5, 0.43, 0.17),
    "girafanokogirikuwagata": Highlight("ながい おおあご", 0.29, 0.3, 0.26),
    "goliathus_goliatus": Highlight("はねの しろと くろの もよう", 0.53, 0.62, 0.19),
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
