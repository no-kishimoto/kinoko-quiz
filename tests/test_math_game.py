"""足し算ゲームの問題作成と進行テスト。"""

import random

import pytest

from src.math_game import KANJI_NUMERALS, create_addition_session, create_subtraction_session


def test_creates_additions_without_carrying():
    session = create_addition_session(random.Random(3))

    assert len(session.questions) == 10
    assert all(question.answer <= 9 for question in session.questions)
    assert all(question.answer in question.choices for question in session.questions)
    assert all(len(set(question.choices)) == 3 for question in session.questions)


def test_creates_single_digit_subtractions_without_negative_answers():
    session = create_subtraction_session(random.Random(9))

    assert len(session.questions) == 10
    assert session.game_name == "ひきざん"
    assert all(question.operation == "subtraction" for question in session.questions)
    assert all(0 <= question.answer <= 9 for question in session.questions)
    assert all(question.left >= question.right for question in session.questions)
    assert all(question.answer in question.choices for question in session.questions)


def test_counts_correct_answer_and_requires_next():
    session = create_addition_session(random.Random(4))

    with pytest.raises(RuntimeError, match="answer the current question"):
        session.next_question()
    assert session.answer(session.question.answer)
    assert session.correct_count == 1
    assert session.next_question() is False


def test_uses_icons_only_on_specified_questions_and_kanji_on_last_three():
    session = create_addition_session(random.Random(5))

    for _ in range(4):
        assert session.shows_icons
        assert not session.uses_kanji_numerals
        session.answer(session.question.answer)
        session.next_question()
    for _ in range(3):
        assert not session.shows_icons
        assert not session.uses_kanji_numerals
        session.answer(session.question.answer)
        session.next_question()
    for _ in range(3):
        assert session.shows_icons
        assert session.uses_kanji_numerals
        assert session.display_number(session.question.left) in KANJI_NUMERALS
        session.answer(session.question.answer)
        session.next_question()
