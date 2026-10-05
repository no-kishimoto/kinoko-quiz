"""Gradioのイベントで、回答と画面遷移が壊れないことを確認する。"""

import base64
import inspect
import random
from pathlib import Path

import gradio as gr
import pytest

from data.kinoko_data import load_kinoko
from src.math_game import create_addition_session
from src.paths import CORRECT_SOUND_PATH, DATA_PATH, INCORRECT_SOUND_PATH, SEARCH_BACKGROUND_DIR
from src.quiz import create_quiz_session
from src.search import create_search_session
from src.ui import build_app


@pytest.fixture(scope="module")
def app():
    return build_app()


def callback(app, name):
    for event in app.fns.values():
        fn = event.fn
        if fn.__name__ == name:
            return fn
        for value in inspect.getclosurevars(fn).nonlocals.values():
            if inspect.isfunction(value) and value.__name__ == name:
                return value
    raise AssertionError(f"Missing callback: {name}")


def assert_sound(updates, path):
    audio = next(value for component, value in updates.items() if isinstance(component, gr.HTML) and isinstance(value, str) and '<audio' in value)
    encoded = audio.split('base64,', 1)[1].split('#play-', 1)[0]
    assert base64.b64decode(encoded) == path.read_bytes()


@pytest.mark.parametrize("correct", [True, False])
def test_math_and_quiz_answers_play_matching_sound(app, correct):
    math = create_addition_session(random.Random(2))
    choice = next(i for i, value in enumerate(math.question.choices) if (value == math.question.answer) == correct)
    updates = callback(app, "answer_math")(math, choice)
    assert_sound(updates, CORRECT_SOUND_PATH if correct else INCORRECT_SOUND_PATH)
    assert not math.answered  # 元のStateを破壊しない。

    quiz = create_quiz_session(load_kinoko(DATA_PATH), 5, random.Random(2))
    choice = next(i for i, item in enumerate(quiz.current_question.choices) if (item == quiz.current_question.answer) == correct)
    updates = callback(app, "answer")(quiz, "kinoko", choice)
    assert_sound(updates, CORRECT_SOUND_PATH if correct else INCORRECT_SOUND_PATH)
    assert quiz.current_result is None


def test_click_after_finding_target_preserves_next_button(app):
    session = create_search_session(load_kinoko(DATA_PATH), tuple(SEARCH_BACKGROUND_DIR.glob('*.png')), random.Random(2))
    assert session.choose_at(session.target.x, session.target.y)
    event = gr.SelectData(None, {"index": (0, 0), "value": None})
    updates = callback(app, "search_click")(session, "kinoko", event)
    assert any(isinstance(component, gr.Button) and value.visible for component, value in updates.items())
    assert any(isinstance(component, gr.State) and value.is_correct and value.correct_count == 1 for component, value in updates.items())
    assert session.is_correct and session.correct_count == 1


def test_search_miss_is_silent_and_does_not_complete_question(app):
    session = create_search_session(load_kinoko(DATA_PATH), tuple(SEARCH_BACKGROUND_DIR.glob('*.png')), random.Random(2))
    event = gr.SelectData(None, {"index": (0, 0), "value": None})
    updates = callback(app, "search_click")(session, "kinoko", event)
    assert not session.is_correct
    assert any(isinstance(component, gr.HTML) and value is None for component, value in updates.items())
    assert any(isinstance(component, gr.Button) and value.visible is False for component, value in updates.items())


def test_image_and_name_open_same_encyclopedia_detail(app):
    events = [f for f in app.fns.values() if f.fn.__name__ == 'open_detail']
    assert len(events) == 6
    for slot in range(3):
        button_event, image_event = events[slot * 2:slot * 2 + 2]
        a = button_event.fn(1, 'kinoko')
        b = image_event.fn(1, 'kinoko')
        assert a.keys() == b.keys()
        for component in a:
            if isinstance(component, gr.Column):
                assert a[component].visible == b[component].visible
            else:
                assert a[component] == b[component]
        assert any(isinstance(component, gr.Image) and Path(value).is_file() for component, value in a.items())


def test_return_to_title_clears_game_states_and_hides_math_and_count(app):
    updates = callback(app, 'return_to_title')()
    assert sum(isinstance(component, gr.State) and value is None for component, value in updates.items()) == 3
    assert sum(isinstance(component, gr.Column) and value.visible is False for component, value in updates.items()) == 3
    assert sum(isinstance(component, gr.Column) and value.visible is True for component, value in updates.items()) == 1


def test_repeated_quiz_selection_does_not_score_twice(app):
    quiz = create_quiz_session(load_kinoko(DATA_PATH), 5, random.Random(2))
    quiz.answer(quiz.current_question.answer.key)
    updates = callback(app, "answer")(quiz, "kinoko", 0)
    assert len(updates) == 1
    assert next(iter(updates.values())) is quiz
    assert quiz.correct_count == 1
