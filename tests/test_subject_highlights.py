from data.subject_data import load_ready_subject_items
from scripts.remove_white_background import KONCHUU_HIGHLIGHTS, SHOKUBUTSU_HIGHLIGHTS
from src.paths import KONCHUU_DATA_PATH, SHOKUBUTSU_DATA_PATH


def test_every_plant_has_an_individual_quiz_highlight():
    assert set(SHOKUBUTSU_HIGHLIGHTS) == {
        item.key for item in load_ready_subject_items(SHOKUBUTSU_DATA_PATH)
    }


def test_every_insect_has_an_individual_quiz_highlight():
    assert set(KONCHUU_HIGHLIGHTS) == {
        item.key for item in load_ready_subject_items(KONCHUU_DATA_PATH)
    }
