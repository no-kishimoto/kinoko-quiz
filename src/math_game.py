"""くり上がりのない足し算ゲームの処理。"""

from __future__ import annotations

import random
from dataclasses import dataclass


QUESTION_COUNT = 10
KANJI_NUMERALS = ("〇", "一", "二", "三", "四", "五", "六", "七", "八", "九")


@dataclass(frozen=True)
class AdditionQuestion:
    left: int
    right: int
    choices: tuple[int, int, int]

    @property
    def answer(self) -> int:
        return self.left + self.right


@dataclass
class AdditionSession:
    questions: tuple[AdditionQuestion, ...]
    current_index: int = 0
    correct_count: int = 0
    answered: bool = False

    @property
    def question(self) -> AdditionQuestion:
        return self.questions[self.current_index]

    @property
    def is_finished(self) -> bool:
        return self.current_index >= len(self.questions)

    @property
    def progress_text(self) -> str:
        return f"もんだい {self.current_index + 1} / {len(self.questions)}"

    @property
    def shows_icons(self) -> bool:
        """1〜4問目と8〜10問目は、数えるアイコンを表示する。"""

        return self.current_index < 4 or self.current_index >= 7

    @property
    def uses_kanji_numerals(self) -> bool:
        """8〜10問目は、漢数字で数を読む問題にする。"""

        return self.current_index >= 7

    def display_number(self, number: int) -> str:
        """問題の段階に応じて、算用数字か漢数字で数を表示する。"""

        return KANJI_NUMERALS[number] if self.uses_kanji_numerals else str(number)

    def answer(self, selected: int) -> bool:
        if self.answered:
            raise RuntimeError("current question is already answered")
        if selected not in self.question.choices:
            raise ValueError("selected value is not one of the choices")
        self.answered = True
        correct = selected == self.question.answer
        if correct:
            self.correct_count += 1
        return correct

    def next_question(self) -> bool:
        if not self.answered:
            raise RuntimeError("answer the current question before continuing")
        self.current_index += 1
        self.answered = False
        return self.is_finished


def create_addition_session(rng: random.Random | None = None) -> AdditionSession:
    randomizer = rng or random.Random()
    pairs = [(left, right) for left in range(1, 9) for right in range(1, 10 - left)]
    selected_pairs = randomizer.sample(pairs, QUESTION_COUNT)
    questions = []
    for left, right in selected_pairs:
        answer = left + right
        pool = [number for number in range(1, 10) if number != answer]
        choices = [answer, *randomizer.sample(pool, 2)]
        randomizer.shuffle(choices)
        questions.append(AdditionQuestion(left, right, tuple(choices)))
    return AdditionSession(tuple(questions))
