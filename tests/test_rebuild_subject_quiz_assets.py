"""Quiz regeneration must not run color-based background removal."""

import json

import pytest
from PIL import Image, ImageDraw

from scripts.rebuild_subject_quiz_assets import rebuild_subject_quiz_assets
from src.images import SILHOUETTE_COLOR


def _fixture(root, *, second=False):
    entries = [{"key": "tanpopo", "name": "たんぽぽ", "quiz_hint": "しろい わたげ", "zukan_text": "はなだよ"}]
    if second:
        entries.append({"key": "tomato", "name": "トマト", "quiz_hint": "あかい み", "zukan_text": "やさいだよ"})
    (root / "data").mkdir()
    (root / "data/shokubutsu.json").write_text(json.dumps(entries), encoding="utf-8")
    color = root / "assets/images/shokubutsu/zukan"
    quiz = root / "assets/images/shokubutsu/quiz"
    color.mkdir(parents=True)
    source = Image.new("RGBA", (80, 80), (255, 255, 255, 0))
    draw = ImageDraw.Draw(source)
    draw.ellipse((8, 8, 72, 72), fill=(255, 255, 255, 255))
    draw.ellipse((30, 30, 50, 50), fill=(255, 255, 255, 0))
    source.putpixel((7, 40), (250, 250, 250, 100))
    source.save(color / "tanpopo.png")
    return source, color, quiz


def test_rebuild_preserves_white_subject_internal_gaps_and_source_bytes(tmp_path):
    source, color, quiz = _fixture(tmp_path)
    before = (color / "tanpopo.png").read_bytes()
    assert rebuild_subject_quiz_assets("shokubutsu", root=tmp_path) == ("tanpopo",)
    assert (color / "tanpopo.png").read_bytes() == before
    with Image.open(quiz / "tanpopo.png") as result:
        assert result.getchannel("A").tobytes() == source.getchannel("A").tobytes()
        assert result.getpixel((40, 40))[3] == 0
        assert result.getpixel((40, 15)) == (255, 255, 255, 255)
        assert result.getpixel((40, 65)) == SILHOUETTE_COLOR
    quiz_bytes = (quiz / "tanpopo.png").read_bytes()
    assert rebuild_subject_quiz_assets("shokubutsu", root=tmp_path) == ()
    assert (quiz / "tanpopo.png").read_bytes() == quiz_bytes


def test_check_only_does_not_create_output_directory(tmp_path):
    _, _, quiz = _fixture(tmp_path)
    assert rebuild_subject_quiz_assets("shokubutsu", root=tmp_path, check_only=True) == ("tanpopo",)
    assert not quiz.exists()


def test_missing_later_input_does_not_write_first_quiz(tmp_path):
    _, _, quiz = _fixture(tmp_path, second=True)
    with pytest.raises(FileNotFoundError):
        rebuild_subject_quiz_assets("shokubutsu", root=tmp_path)
    assert not quiz.exists()


def test_unknown_key_and_opaque_input_are_rejected_without_writing(tmp_path):
    _, color, quiz = _fixture(tmp_path)
    with pytest.raises(ValueError, match="unknown keys"):
        rebuild_subject_quiz_assets("shokubutsu", root=tmp_path, keys=("not_in_catalogue",))
    Image.new("RGBA", (80, 80), (255, 255, 255, 255)).save(color / "tanpopo.png")
    with pytest.raises(ValueError, match="transparent cutout"):
        rebuild_subject_quiz_assets("shokubutsu", root=tmp_path)
    assert not quiz.exists()


def test_rebuild_keeps_one_level_corner_noise_and_antialiased_edge_unchanged(tmp_path):
    source, color, quiz = _fixture(tmp_path)
    source.putpixel((0, 0), (0, 255, 0, 1))
    source.save(color / "tanpopo.png")
    original_bytes = (color / "tanpopo.png").read_bytes()
    rebuild_subject_quiz_assets("shokubutsu", root=tmp_path)
    assert (color / "tanpopo.png").read_bytes() == original_bytes
    with Image.open(quiz / "tanpopo.png") as result:
        assert result.getchannel("A").tobytes() == source.getchannel("A").tobytes()
        assert result.getpixel((0, 0))[3] == 1
        assert result.getpixel((7, 40))[3] == 100


def test_rebuild_rejects_corner_alpha_above_one_without_writing(tmp_path):
    source, color, quiz = _fixture(tmp_path)
    source.putpixel((0, 0), (0, 255, 0, 2))
    source.save(color / "tanpopo.png")
    with pytest.raises(ValueError, match="transparent cutout"):
        rebuild_subject_quiz_assets("shokubutsu", root=tmp_path)
    assert not quiz.exists()
