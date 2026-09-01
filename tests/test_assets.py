"""画像・音声素材のテスト。"""

from PIL import Image

from data.kinoko_data import Highlight
from src.images import SILHOUETTE_COLOR, create_quiz_image


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
