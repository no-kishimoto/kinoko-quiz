"""きのこ探しのあたり判定と進行テスト。"""

from src.search import TARGETS, SearchSession, status_text, targets_text


def test_finds_each_target_once():
    session = SearchSession()

    for target in TARGETS:
        assert session.find_at(target.x, target.y) == target
    assert session.is_finished
    assert session.found_count == 3
    assert session.find_at(TARGETS[0].x, TARGETS[0].y) is None


def test_missing_click_does_not_change_progress():
    session = SearchSession()

    assert session.find_at(0.01, 0.01) is None
    assert session.found_count == 0
    assert "あと 3こ" in status_text(session)
    assert "まだだよ" in targets_text(session)
