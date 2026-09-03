"""足し算ゲームの問題作成と進行テスト。"""

import random

import pytest

from src.math_game import create_addition_session


def test_creates_additions_without_carrying():
    session = create_addition_session(random.Random(3))

    assert len(session.questions) == 5
    assert all(question.answer <= 9 for question in session.questions)
    assert all(question.answer in question.choices for question in session.questions)
    assert all(len(set(question.choices)) == 3 for question in session.questions)


def test_counts_correct_answer_and_requires_next():
    session = create_addition_session(random.Random(4))

    with pytest.raises(RuntimeError, match="answer the current question"):
        session.next_question()
    assert session.answer(session.question.answer)
    assert session.correct_count == 1
    assert session.next_question() is False


def test_hides_mushroom_count_on_fifth_question():
    session = create_addition_session(random.Random(5))

    for _ in range(4):
        assert session.shows_mushrooms
        session.answer(session.question.answer)
        session.next_question()
    assert not session.shows_mushrooms
