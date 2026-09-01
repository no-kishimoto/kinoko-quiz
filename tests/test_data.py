"""きのこデータの読込と検証のテスト。"""

import json

import pytest

from data.kinoko_data import KinokoDataError, load_kinoko


def valid_entry() -> dict:
    return {
        "key": "sample",
        "name": "さんぷるたけ",
        "habitat": "もりの なか",
        "season": "なつ",
        "size": "5センチくらい",
        "color": "あか",
        "features": "かさが まるい",
        "quiz_hint": "まるい かさ",
        "toxicity": "non_poisonous",
        "edibility": "edible",
        "caution": "よく ひを とおす",
        "similar_kinoko": "にたきのこ",
        "cooking": "やいて たべる",
        "trivia": "あめの あとに でる",
        "highlight": {
            "part": "かさの まんなか",
            "x": 0.5,
            "y": 0.35,
            "radius": 0.12,
        },
    }


def write_data(tmp_path, entries: list[dict]):
    path = tmp_path / "kinoko.json"
    path.write_text(json.dumps(entries, ensure_ascii=False), encoding="utf-8")
    return path


def test_loads_valid_data(tmp_path):
    kinoko = load_kinoko(write_data(tmp_path, [valid_entry()]))
    assert len(kinoko) == 1
    assert kinoko[0].key == "sample"
    assert kinoko[0].image_filename == "sample.png"


def test_rejects_duplicate_keys(tmp_path):
    first = valid_entry()
    second = {**valid_entry(), "name": "べつの きのこ"}
    with pytest.raises(KinokoDataError, match="keys must be unique"):
        load_kinoko(write_data(tmp_path, [first, second]))


def test_rejects_kanji_in_visible_text(tmp_path):
    entry = {**valid_entry(), "habitat": "森の なか"}
    with pytest.raises(KinokoDataError, match="must not contain kanji"):
        load_kinoko(write_data(tmp_path, [entry]))


def test_rejects_invalid_highlight(tmp_path):
    entry = {
        **valid_entry(),
        "highlight": {
            "part": "かさの まんなか",
            "x": 1.2,
            "y": 0.5,
            "radius": 0.1,
        },
    }
    with pytest.raises(KinokoDataError, match="between 0 and 1"):
        load_kinoko(write_data(tmp_path, [entry]))


def test_requires_cooking_for_edible_mushroom(tmp_path):
    entry = {**valid_entry(), "cooking": None}
    with pytest.raises(KinokoDataError, match="require cooking"):
        load_kinoko(write_data(tmp_path, [entry]))
