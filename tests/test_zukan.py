"""図鑑のページ分けと詳細表示のテスト。"""

from pathlib import Path

import pytest

from data.kinoko_data import load_kinoko
from data.subject_data import load_ready_subject_items
from src.zukan import PAGE_SIZE, page_count, zukan_detail_text, zukan_page

DATA_PATH = Path(__file__).parents[1] / "data" / "kinoko.json"


def test_splits_thirty_mushrooms_into_ten_pages():
    kinoko = load_kinoko(DATA_PATH)

    assert page_count(kinoko) == 10
    first = zukan_page(kinoko, 0)
    last = zukan_page(kinoko, 9)

    assert len(first.items) == PAGE_SIZE
    assert first.page_text == "1 / 10"
    assert not first.has_previous
    assert first.has_next
    assert len(last.items) == PAGE_SIZE
    assert last.page_text == "10 / 10"
    assert last.has_previous
    assert not last.has_next


def test_bounds_page_index_and_rejects_invalid_page_size():
    kinoko = load_kinoko(DATA_PATH)

    assert zukan_page(kinoko, -1).index == 0
    assert zukan_page(kinoko, 99).index == 9
    with pytest.raises(ValueError, match="at least 1"):
        page_count(kinoko, 0)


def test_detail_includes_cooking_only_when_available():
    kinoko = load_kinoko(DATA_PATH)
    edible = next(item for item in kinoko if item.key == "shiitake")
    unknown = next(item for item in kinoko if item.key == "sorairotake")

    assert "### たべかた" in zukan_detail_text(edible, "どくなし")
    assert "### たべかた" not in zukan_detail_text(unknown, "どくが あるか わかっていない")


def test_subject_detail_has_feature_and_encyclopedia_note():
    item = load_ready_subject_items(DATA_PATH.with_name("shokubutsu.json"))[0]

    detail = zukan_detail_text(item)

    assert "### とくちょう" in detail
    assert "### ずかんメモ" in detail
    assert item.quiz_hint in detail
    assert item.zukan_text in detail
