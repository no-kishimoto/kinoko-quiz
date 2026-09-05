from pathlib import Path
import random

from data.subject_data import load_ready_subject_items
from src.quiz import create_quiz_session
from src.search import create_search_session, render_scene
from src.zukan import page_count, zukan_page


ROOT = Path(__file__).parents[1]
ITEMS = load_ready_subject_items(ROOT / "data" / "konchuu.json")


def test_ready_insects_have_both_game_images():
    for item in ITEMS:
        assert (ROOT / "assets" / "images" / "konchuu" / "zukan" / item.image_filename).is_file()
        assert (ROOT / "assets" / "images" / "konchuu" / "quiz" / item.image_filename).is_file()


def test_ready_insects_work_in_quiz_zukan_and_search():
    quiz = create_quiz_session(ITEMS, 5, random.Random(2))
    assert all(question.answer.key in question.choice_keys for question in quiz.questions)
    assert page_count(ITEMS) == 7
    assert len(zukan_page(ITEMS, 0).items) == 3

    backgrounds = (ROOT / "assets" / "images" / "search" / "backgrounds" / "roots.png",)
    session = create_search_session(ITEMS, backgrounds, random.Random(3))
    image = render_scene(session, ROOT / "assets" / "images" / "konchuu" / "zukan")
    assert image.size[0] > 0
