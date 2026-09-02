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
