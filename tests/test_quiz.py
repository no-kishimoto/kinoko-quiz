"""クイズ処理のテスト。"""

import random
from pathlib import Path

import pytest

from data.kinoko_data import load_kinoko
from src.quiz import create_quiz_session

DATA_PATH = Path(__file__).parents[1] / "data" / "kinoko.json"


def test_creates_five_unique_questions_with_three_choices():
    kinoko = load_kinoko(DATA_PATH)
    session = create_quiz_session(kinoko, 5, random.Random(7))

    answer_keys = [question.answer.key for question in session.questions]
    assert len(answer_keys) == 5
    assert len(set(answer_keys)) == 5
    assert all(len(set(question.choice_keys)) == 3 for question in session.questions)
    assert all(question.answer.key in question.choice_keys for question in session.questions)


def test_answer_is_counted_only_once_and_next_requires_answer():
    kinoko = load_kinoko(DATA_PATH)
    session = create_quiz_session(kinoko, 5, random.Random(3))

    with pytest.raises(RuntimeError, match="answer the current question"):
        session.next_question()

    answer_key = session.current_question.answer.key
    result = session.answer(answer_key)
    assert result.is_correct
    assert session.correct_count == 1

    with pytest.raises(RuntimeError, match="already answered"):
        session.answer(answer_key)

    assert session.next_question() is False
    assert session.current_index == 1
    assert session.correct_count == 1


def test_rejects_unsupported_question_count():
    kinoko = load_kinoko(DATA_PATH)
    with pytest.raises(ValueError, match="must be 5 or 10"):
        create_quiz_session(kinoko, 7, random.Random(1))
