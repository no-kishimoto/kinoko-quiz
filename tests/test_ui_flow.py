"""Gradioのイベントで、回答と画面遷移が壊れないことを確認する。"""

import base64
import inspect
import random
from pathlib import Path

import gradio as gr
import pytest

from data.kinoko_data import load_kinoko
from data.subject_data import load_ready_subject_items
from src.math_game import create_addition_session
from src.paths import (
    CORRECT_SOUND_PATH, DATA_PATH, INCORRECT_SOUND_PATH, KYOURYUU_DATA_PATH,
    KYOURYUU_FOSSIL_IMAGE_DIR, KYOURYUU_RECONSTRUCTION_IMAGE_DIR, SEARCH_BACKGROUND_DIR,
)
from src.quiz import QuizQuestion, create_quiz_session
from src.search import create_search_session
from src.ui import APP_CSS, build_app


APPROVED_ADDITION_HINTS = {
    "coelacanth": "ひれの つけねが ふとい。",
    "ankylosaurus": "かたい よろい。しっぽの さきに おおきな かたまり。",
    "parasaurolophus": "あたまから うしろへ のびる ながい とさか。",
    "trilobite": "からだに たくさんの ふし。そとが かたい から。",
    "anomalocaris": "おおきな め。からだの よこに ならぶ ひれ。",
    "ottoia": "ながい からだに たくさんの しわ。",
    "mammoth": "ながく まがった 2ほんの きば。4ほんの あし。",
    "smilodon": "うえの あごから のびる ながい 2ほんの きば。",
}


def test_quiz_explanation_text_stays_readable_on_the_light_game_background():
    rule = APP_CSS.split('.explanation-card, .explanation-card * {', 1)[1].split('}', 1)[0]
    assert 'color: #000000 !important;' in rule
    assert 'font-size: 1.3rem !important;' in rule
    assert 'line-height: 1.45 !important;' in rule


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
    assert any(isinstance(component, gr.HTML) and value == gr.skip() for component, value in updates.items())
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


@pytest.mark.parametrize("correct", [True, False])
@pytest.mark.parametrize("question_count", [5, 10])
def test_dinosaur_quiz_uses_names_and_replaces_specimen_without_duplicate_image(app, correct, question_count):
    updates = callback(app, "start_quiz")(question_count, "kyouryuu")
    session = next(value for component, value in updates.items() if isinstance(component, gr.State))
    image = next(component for component in updates if isinstance(component, gr.Image) and "quiz-image" in component.elem_classes)
    choices = [component for component in updates if isinstance(component, gr.Button) and "choice" in component.elem_classes]
    assert len(choices) == 3
    assert [updates[button].value for button in choices] == [item.name for item in session.current_question.choices]
    assert all(updates[button].visible and updates[button].interactive for button in choices)
    assert "fossil" in str(updates[image])
    assert not any("dinosaur-reconstruction" in component.elem_classes for component in app.blocks.values())
    assert not any(isinstance(component, gr.Gallery) for component in app.blocks.values())

    for question_index in range(question_count):
        answer_item = session.current_question.answer
        choice_index = next(i for i, item in enumerate(session.current_question.choices) if (item.key == answer_item.key) == correct)
        answered = callback(app, "answer")(session, "kyouryuu", choice_index)
        displayed = Path(answered[image])
        assert displayed.name == answer_item.image_filename
        assert displayed.read_bytes() == (KYOURYUU_RECONSTRUCTION_IMAGE_DIR / answer_item.image_filename).read_bytes()
        session = next(value for component, value in answered.items() if isinstance(component, gr.State))
        advanced = callback(app, "go_next")(session, "kyouryuu")
        session = next(value for component, value in advanced.items() if isinstance(component, gr.State))
        if question_index < question_count - 1:
            assert "fossil" in str(advanced[image])
            assert [advanced[button].value for button in choices] == [item.name for item in session.current_question.choices]
            assert all(advanced[button].visible and advanced[button].interactive for button in choices)
        else:
            assert session.is_finished
            assert session.correct_count == (question_count if correct else 0)


@pytest.mark.parametrize("key, approved_hint", APPROVED_ADDITION_HINTS.items())
@pytest.mark.parametrize("correct", [True, False])
def test_each_added_dinosaur_swaps_approved_images_and_shows_approved_text(app, monkeypatch, key, approved_hint, correct):
    def create_session_with_first_addition(items, count):
        session = create_quiz_session(items, count, random.Random(2))
        answer_item = next(item for item in items if item.key == key)
        first = QuizQuestion(answer=answer_item, choices=(items[0], answer_item, items[1]))
        remaining = tuple(question for question in session.questions if question.answer.key != key)
        session.questions = (first, *remaining[:count - 1])
        return session

    monkeypatch.setattr("src.ui.create_quiz_session", create_session_with_first_addition)
    started = callback(app, "start_quiz")(5, "kyouryuu")
    session = next(value for component, value in started.items() if isinstance(component, gr.State))
    item = session.current_question.answer
    assert item.key == key
    image = next(component for component in started if isinstance(component, gr.Image) and "quiz-image" in component.elem_classes)
    hint = next(component for component in started if isinstance(component, gr.Markdown) and "hint-card" in component.elem_classes)
    explanation = next(component for component in started if isinstance(component, gr.Markdown) and "explanation-card" in component.elem_classes)
    choices = [component for component in started if isinstance(component, gr.Button) and "choice" in component.elem_classes]
    assert Path(started[image]) == KYOURYUU_FOSSIL_IMAGE_DIR / item.image_filename
    assert started[hint] == f"### かたちの ヒント\n{approved_hint}"
    assert started[explanation].visible is False
    assert started[explanation].value == ""
    assert [started[button].value for button in choices] == [choice.name for choice in session.current_question.choices]

    choice_index = next(i for i, choice in enumerate(session.current_question.choices) if (choice.key == key) == correct)
    answered = callback(app, "answer")(session, "kyouryuu", choice_index)
    reconstruction = KYOURYUU_RECONSTRUCTION_IMAGE_DIR / item.image_filename
    assert Path(answered[image]) == reconstruction
    assert Path(started[image]).read_bytes() != reconstruction.read_bytes()
    assert answered[explanation].visible is True
    assert answered[explanation].value == f"### {item.name}\n\n{item.zukan_text}"
    assert all(answered[button].interactive is False for button in choices)
    assert_sound(answered, CORRECT_SOUND_PATH if correct else INCORRECT_SOUND_PATH)
    updated = next(value for component, value in answered.items() if isinstance(component, gr.State))
    assert updated.current_result.is_correct is correct
    assert session.current_result is None

    advanced = callback(app, "go_next")(updated, "kyouryuu")
    next_session = next(value for component, value in advanced.items() if isinstance(component, gr.State))
    assert Path(advanced[image]) == KYOURYUU_FOSSIL_IMAGE_DIR / next_session.current_question.answer.image_filename
    assert advanced[hint] == f"### かたちの ヒント\n{next_session.current_question.answer.quiz_hint}"
    assert advanced[explanation].visible is False
    assert advanced[explanation].value == ""
    assert all(advanced[button].visible and advanced[button].interactive for button in choices)


def test_dinosaur_encyclopedia_has_three_columns_and_six_pages_reaching_all_eighteen_details(app):
    items = load_ready_subject_items(KYOURYUU_DATA_PATH)
    show_zukan = callback(app, "show_zukan")
    detail_events = [event for event in app.fns.values() if event.fn.__name__ == "open_detail"]
    assert len(detail_events) == 6
    grids = [component for component in app.blocks.values() if isinstance(component, gr.Row) and "zukan-grid" in component.elem_classes]
    assert len(grids) == 1
    assert len([component for component in grids[0].children if isinstance(component, gr.Column)]) == 3
    seen_names = []

    for page_index in range(6):
        shown = show_zukan(page_index, "kyouryuu")
        images = [component for component in shown if isinstance(component, gr.Image)]
        names = [component for component in shown if isinstance(component, gr.Button) and "main-button" not in component.elem_classes]
        assert len(images) == len(names) == 3
        assert tuple(shown[button].value for button in names) == tuple(item.name for item in items[page_index * 3:page_index * 3 + 3])
        assert any(isinstance(component, gr.Markdown) and value == f"{page_index + 1} / 6" for component, value in shown.items())
        for slot, item in enumerate(items[page_index * 3:page_index * 3 + 3]):
            assert shown[names[slot]].visible is True
            assert shown[images[slot]].visible is True
            assert Path(shown[images[slot]].value["path"]).read_bytes() == (KYOURYUU_RECONSTRUCTION_IMAGE_DIR / item.image_filename).read_bytes()
            detail = detail_events[slot * 2].fn(page_index, "kyouryuu")
            image_detail = detail_events[slot * 2 + 1].fn(page_index, "kyouryuu")
            assert any(isinstance(component, gr.Markdown) and value == f"# {item.name}" for component, value in detail.items())
            assert any(isinstance(component, gr.Markdown) and value == f"### とくちょう\n{item.quiz_hint}\n\n### ずかんメモ\n{item.zukan_text}" for component, value in detail.items())
            for component, value in detail.items():
                if isinstance(component, gr.Image):
                    assert Path(value).read_bytes() == (KYOURYUU_RECONSTRUCTION_IMAGE_DIR / item.image_filename).read_bytes()
                    assert image_detail[component] == value
            seen_names.append(item.name)

    assert len(seen_names) == len(set(seen_names)) == 18
    assert tuple(seen_names) == tuple(item.name for item in items)
