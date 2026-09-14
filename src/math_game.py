"""一桁のたしざん・ひきざんゲームの処理。"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Literal


QUESTION_COUNT = 10
KANJI_NUMERALS = ("〇", "一", "二", "三", "四", "五", "六", "七", "八", "九")
Operation = Literal["addition", "subtraction"]


@dataclass(frozen=True)
class ArithmeticQuestion:
    left: int
    right: int
    choices: tuple[int, int, int]
    operation: Operation

    @property
    def answer(self) -> int:
        return self.left + self.right if self.operation == "addition" else self.left - self.right

    @property
    def symbol(self) -> str:
        return "＋" if self.operation == "addition" else "－"


@dataclass
class ArithmeticSession:
    questions: tuple[ArithmeticQuestion, ...]
    game_name: str
    current_index: int = 0
    correct_count: int = 0
    answered: bool = False

    @property
    def question(self) -> ArithmeticQuestion:
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


def _create_session(operation: Operation, rng: random.Random | None = None) -> ArithmeticSession:
    randomizer = rng or random.Random()
    if operation == "addition":
        pairs = [(left, right) for left in range(1, 9) for right in range(1, 10 - left)]
        game_name = "たしざん"
    else:
        pairs = [(left, right) for left in range(1, 10) for right in range(1, left + 1)]
        game_name = "ひきざん"
    selected_pairs = randomizer.sample(pairs, QUESTION_COUNT)
    questions = []
    for left, right in selected_pairs:
        answer = left + right if operation == "addition" else left - right
        pool = [number for number in range(10) if number != answer]
        choices = [answer, *randomizer.sample(pool, 2)]
        randomizer.shuffle(choices)
        questions.append(ArithmeticQuestion(left, right, tuple(choices), operation))
    return ArithmeticSession(tuple(questions), game_name)


def create_addition_session(rng: random.Random | None = None) -> ArithmeticSession:
    return _create_session("addition", rng)


def create_subtraction_session(rng: random.Random | None = None) -> ArithmeticSession:
    return _create_session("subtraction", rng)
