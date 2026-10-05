"""図鑑・クイズの素材が欠けたり、背景で形が変わったりしないことを検証する。"""

import pytest
from PIL import Image, ImageChops

from data.kinoko_data import load_kinoko
from data.subject_data import load_ready_subject_items
from src.images import SILHOUETTE_COLOR
from src.paths import (
    DATA_PATH, QUIZ_IMAGE_DIR, ZUKAN_IMAGE_DIR,
    SHOKUBUTSU_DATA_PATH, SHOKUBUTSU_QUIZ_IMAGE_DIR, SHOKUBUTSU_ZUKAN_IMAGE_DIR,
    KONCHUU_DATA_PATH, KONCHUU_QUIZ_IMAGE_DIR, KONCHUU_ZUKAN_IMAGE_DIR,
)


@pytest.mark.parametrize("items,color_dir,quiz_dir", [
    (load_kinoko(DATA_PATH), ZUKAN_IMAGE_DIR, QUIZ_IMAGE_DIR),
    (load_ready_subject_items(SHOKUBUTSU_DATA_PATH), SHOKUBUTSU_ZUKAN_IMAGE_DIR, SHOKUBUTSU_QUIZ_IMAGE_DIR),
    (load_ready_subject_items(KONCHUU_DATA_PATH), KONCHUU_ZUKAN_IMAGE_DIR, KONCHUU_QUIZ_IMAGE_DIR),
], ids=["kinoko", "shokubutsu", "konchuu"])
def test_all_quiz_assets_preserve_subject_shape_and_have_visible_color_hint(items, color_dir, quiz_dir):
    for item in items:
        with Image.open(color_dir / item.image_filename) as source, Image.open(quiz_dir / item.image_filename) as quiz:
            source = source.convert("RGBA")
            quiz = quiz.convert("RGBA")
            assert source.size == quiz.size, item.key
            alpha = source.getchannel("A")
            assert alpha.getbbox() is not None, item.key
            assert alpha.tobytes() == quiz.getchannel("A").tobytes(), item.key
            # 透明な画素のRGB値は数えず、実際に見えるヒントだけを調べる。
            silhouette = Image.new("RGB", quiz.size, SILHOUETTE_COLOR[:3])
            difference = ImageChops.difference(quiz.convert("RGB"), silhouette).convert("L")
            visible_difference = ImageChops.multiply(difference, alpha)
            assert visible_difference.getbbox() is not None, item.key
