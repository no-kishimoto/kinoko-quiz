"""旧背景除去の入口は、明示的な指定がない限り画像を変更しない。"""

import sys

import pytest
from PIL import Image

from scripts import remove_white_background as legacy


@pytest.fixture
def mocked_rebuilds(monkeypatch, tmp_path):
    # 本物の素材には触れない。ディスパッチの呼出しだけを記録する。
    sample = tmp_path / "white-petal.png"
    Image.new("RGBA", (8, 8), (255, 255, 255, 255)).save(sample)
    before = sample.read_bytes()
    calls = []
    monkeypatch.setattr(
        legacy, "rebuild_subject_assets",
        lambda *args: calls.append(("subject", args)),
    )
    monkeypatch.setattr(
        legacy, "rebuild_kinoko_assets",
        lambda: calls.append(("kinoko", ())),
    )
    return calls, sample, before


@pytest.mark.parametrize("argv", [[], None], ids=["explicit-empty", "command-line-empty"])
def test_no_argument_does_not_dispatch_or_change_images(argv, mocked_rebuilds, monkeypatch, capsys):
    calls, sample, before = mocked_rebuilds
    monkeypatch.setattr(sys, "argv", ["remove_white_background.py"])

    assert legacy.main(argv) == 2

    assert calls == []
    assert sample.read_bytes() == before
    assert "画像は変更していません" in capsys.readouterr().err


def test_help_does_not_dispatch_or_change_images(mocked_rebuilds, capsys):
    calls, sample, before = mocked_rebuilds

    with pytest.raises(SystemExit) as stopped:
        legacy.main(["--help"])

    assert stopped.value.code == 0
    assert calls == []
    assert sample.read_bytes() == before
    assert "--legacy-color-threshold-removal" in capsys.readouterr().out


def test_abbreviated_flag_cannot_enable_legacy_removal(mocked_rebuilds):
    calls, sample, before = mocked_rebuilds

    with pytest.raises(SystemExit) as stopped:
        legacy.main(["--legacy"])

    assert stopped.value.code == 2
    assert calls == []
    assert sample.read_bytes() == before


def test_only_explicit_legacy_flag_dispatches_all_three_rebuilds(mocked_rebuilds):
    calls, sample, before = mocked_rebuilds

    assert legacy.main(["--legacy-color-threshold-removal"]) == 0

    assert calls == [
        ("subject", (
            legacy.SHOKUBUTSU_DATA_PATH,
            legacy.SHOKUBUTSU_ZUKAN_IMAGE_DIR,
            legacy.SHOKUBUTSU_QUIZ_IMAGE_DIR,
            legacy.SHOKUBUTSU_HIGHLIGHTS,
        )),
        ("subject", (
            legacy.KONCHUU_DATA_PATH,
            legacy.KONCHUU_ZUKAN_IMAGE_DIR,
            legacy.KONCHUU_QUIZ_IMAGE_DIR,
            legacy.KONCHUU_HIGHLIGHTS,
        )),
        ("kinoko", ()),
    ]
    assert sample.read_bytes() == before
