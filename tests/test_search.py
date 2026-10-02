"""きのこ探しのあたり判定と進行テスト。"""

from pathlib import Path
import random

from data.kinoko_data import load_kinoko
from src.search import create_search_session, render_scene, status_text

ROOT = Path(__file__).parents[1]
KINOKO = load_kinoko(ROOT / "data" / "kinoko.json")
BACKGROUNDS = (ROOT / "assets" / "images" / "search" / "backgrounds" / "roots.png",)


def test_finds_only_the_specified_target():
    session = create_search_session(KINOKO, BACKGROUNDS, random.Random(1))

    decoy = session.decoys[0]
    assert session.choose_at(decoy.x, decoy.y) is False
    assert not session.is_correct
    assert session.choose_at(session.target.x, session.target.y) is True
    assert session.is_correct
    assert session.correct_count == 1
    assert session.choose_at(session.target.x, session.target.y) is False


def test_missing_click_keeps_question_open():
    session = create_search_session(KINOKO, BACKGROUNDS, random.Random(1))

    assert session.choose_at(0.01, 0.01) is False
    assert not session.is_correct
    assert "もりの なか" in status_text(session)


def test_can_choose_all_thirty_mushrooms_and_render_scene():
    seen = set()
    for seed in range(1000):
        session = create_search_session(KINOKO, BACKGROUNDS, random.Random(seed))
        seen.add(session.target.item.key)
    assert seen == {item.key for item in KINOKO}

    session = create_search_session(KINOKO, BACKGROUNDS, random.Random(4))
    image = render_scene(session, ROOT / "assets" / "images" / "zukan")
    assert image.size[0] > 0


def test_search_game_has_five_questions_and_counts_each_correct_answer():
    session = create_search_session(KINOKO, BACKGROUNDS, random.Random(8), current_index=4, correct_count=4)

    assert session.total_questions == 5
    assert session.progress_text == "もんだい 5 / 5"
    assert session.is_last_question
    assert session.choose_at(session.target.x, session.target.y)
    assert session.correct_count == 5
