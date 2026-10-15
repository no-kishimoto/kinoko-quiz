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


def _assert_cutout_alpha_contract(image, label):
    """切り抜き素材の最低条件。内部の消し残しの正しさは目視でも確認する。"""

    alpha = image.getchannel("A")
    # getbbox() だけでは、背景まで不透明な四角い画像も通過してしまう。
    # 白い花や翅も本体なので、RGB の色から背景かどうかは判定しない。
    assert alpha.getextrema() == (0, 255), f"{label}: transparent background and opaque subject required"
    width, height = image.size
    corners = ((0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1))
    # 生成PNGを再加工せず保持する。1/255だけの量子化誤差は許容するが、
    # 不透明な背景や、本体全体の半透明化は許容しない。
    assert all(alpha.getpixel(point) <= 1 for point in corners), f"{label}: corners must be transparent"


@pytest.mark.parametrize("fill", [
    (255, 255, 255, 255),
    (0, 0, 0, 0),
    (100, 180, 80, 128),
], ids=["opaque-background", "empty-image", "no-opaque-subject"])
def test_cutout_alpha_contract_rejects_invalid_assets(fill):
    with pytest.raises(AssertionError):
        _assert_cutout_alpha_contract(Image.new("RGBA", (8, 8), fill), "sample")


def test_cutout_alpha_contract_rejects_an_opaque_rectangle_with_a_transparent_pixel():
    image = Image.new("RGBA", (8, 8), (255, 255, 255, 255))
    image.putpixel((4, 4), (255, 255, 255, 0))

    with pytest.raises(AssertionError, match="corners"):
        _assert_cutout_alpha_contract(image, "sample")


def test_cutout_alpha_contract_preserves_subvisible_generated_alpha_noise():
    image = Image.new("RGBA", (8, 8), (255, 255, 255, 0))
    image.putpixel((4, 4), (255, 255, 255, 255))
    image.putpixel((0, 0), (0, 255, 0, 1))
    _assert_cutout_alpha_contract(image, "generated sample")


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
            _assert_cutout_alpha_contract(source, item.key)
            alpha = source.getchannel("A")
            assert alpha.tobytes() == quiz.getchannel("A").tobytes(), item.key
            # 透明な画素のRGB値は数えず、実際に見えるヒントだけを調べる。
            silhouette = Image.new("RGB", quiz.size, SILHOUETTE_COLOR[:3])
            difference = ImageChops.difference(quiz.convert("RGB"), silhouette).convert("L")
            visible_difference = ImageChops.multiply(difference, alpha)
            assert visible_difference.getbbox() is not None, item.key
