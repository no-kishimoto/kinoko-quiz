"""きのこ探しのあたり判定と進行テスト。"""

import random

from src.search import SEARCH_QUESTIONS, SearchSession, create_search_session, status_text, targets_text


def test_finds_each_target_once():
    session = SearchSession(SEARCH_QUESTIONS[0])

    for target in session.question.targets:
        assert session.find_at(target.x, target.y) == target
    assert session.is_finished
    assert session.found_count == 3
    first = session.question.targets[0]
    assert session.find_at(first.x, first.y) is None


def test_missing_click_does_not_change_progress():
    session = SearchSession(SEARCH_QUESTIONS[0])

    assert session.find_at(0.01, 0.01) is None
    assert session.found_count == 0
    assert "あと 3こ" in status_text(session)
    assert "まだだよ" in targets_text(session)


def test_has_fifteen_questions_and_can_choose_one():
    assert len(SEARCH_QUESTIONS) == 15
    session = create_search_session(rng=random.Random(3))
    assert session.question in SEARCH_QUESTIONS
    assert len(session.question.targets) == 3
