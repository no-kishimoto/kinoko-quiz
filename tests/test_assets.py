"""画像・音声素材のテスト。"""

import pytest
from PIL import Image, ImageDraw

from data.kinoko_data import Highlight
from src.images import SILHOUETTE_COLOR, create_quiz_image, save_quiz_image


def test_quiz_image_keeps_only_highlight_in_color():
    source = Image.new("RGBA", (100, 100), (220, 80, 40, 255))
    highlight = Highlight(part="かさ", x=0.5, y=0.5, radius=0.2)

    result = create_quiz_image(source, highlight)

    assert result.getpixel((50, 50)) == (220, 80, 40, 255)
    assert result.getpixel((5, 5)) == SILHOUETTE_COLOR


def test_quiz_image_preserves_transparency():
    source = Image.new("RGBA", (20, 20), (220, 80, 40, 255))
    source.putpixel((0, 0), (0, 0, 0, 0))
    highlight = Highlight(part="かさ", x=0.5, y=0.5, radius=0.2)

    result = create_quiz_image(source, highlight)

    assert result.getpixel((0, 0))[3] == 0


@pytest.mark.parametrize("subject_color", [
    (255, 255, 255, 255),
    (236, 236, 236, 255),
    (235, 250, 255, 255),
], ids=["white-petal-or-wing", "pale-gray-subject", "pale-blue-subject"])
def test_quiz_image_keeps_pale_subject_opaque_and_enclosed_gaps_transparent(subject_color, tmp_path):
    # 葉・脚の間の隙間は端とつながらなくても透明。本体と隙間を
    # RGB の明るさで区別せず、確認済みのアルファをそのまま使う。
    source = Image.new("RGBA", (64, 64), (255, 255, 255, 0))
    draw = ImageDraw.Draw(source)
    draw.ellipse((8, 8, 56, 56), fill=subject_color)
    draw.ellipse((24, 24, 40, 40), fill=(255, 255, 255, 0))
    source.putpixel((7, 32), (*subject_color[:3], 96))
    highlight = Highlight(part="はな・はね", x=0.72, y=0.5, radius=0.2)

    result = create_quiz_image(source, highlight)
    saved_path = save_quiz_image(source, highlight, tmp_path / "quiz.png")
    with Image.open(saved_path) as saved:
        assert saved.convert("RGBA").tobytes() == result.tobytes()

    assert result.getchannel("A").tobytes() == source.getchannel("A").tobytes()
    assert result.getpixel((18, 32)) == SILHOUETTE_COLOR
    assert result.getpixel((46, 32)) == subject_color
    assert result.getpixel((32, 32))[3] == 0
    assert result.getpixel((7, 32))[3] == 96
    for background_color in ((30, 110, 220, 255), (255, 80, 160, 255)):
        background = Image.new("RGBA", result.size, background_color)
        preview = Image.alpha_composite(background, result)
        assert preview.getpixel((32, 32)) == background_color
        assert preview.getpixel((0, 0)) == background_color
        assert preview.getpixel((46, 32)) == subject_color
