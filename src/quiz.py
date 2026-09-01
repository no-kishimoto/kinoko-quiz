"""クイズの抽選、3択、正誤判定、進行状態。"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Sequence

from data.kinoko_data import Kinoko

QUESTION_COUNTS = (5, 10)


@dataclass(frozen=True)
class QuizQuestion:
    """正解1つと、表示順を確定した3つの選択肢。"""

    answer: Kinoko
    choices: tuple[Kinoko, Kinoko, Kinoko]

    @property
    def choice_keys(self) -> tuple[str, str, str]:
        return tuple(choice.key for choice in self.choices)


@dataclass(frozen=True)
class AnswerResult:
    """1問分の回答結果。"""

    is_correct: bool
    answer: Kinoko
    selected_key: str


@dataclass
class QuizSession:
    """1回のクイズの進行状態。"""

    questions: tuple[QuizQuestion, ...]
    current_index: int = 0
    correct_count: int = 0
    current_result: AnswerResult | None = None

    @property
    def total_questions(self) -> int:
        return len(self.questions)

    @property
    def is_finished(self) -> bool:
        return self.current_index >= self.total_questions

    @property
    def current_question(self) -> QuizQuestion:
        if self.is_finished:
            raise RuntimeError("quiz is already finished")
        return self.questions[self.current_index]

    @property
    def progress_text(self) -> str:
        if self.is_finished:
            return f"もんだい {self.total_questions} / {self.total_questions}"
        return f"もんだい {self.current_index + 1} / {self.total_questions}"

    def answer(self, selected_key: str) -> AnswerResult:
        """現在の問題へ1回だけ回答する。"""

        if self.is_finished:
            raise RuntimeError("quiz is already finished")
        if self.current_result is not None:
            raise RuntimeError("current question is already answered")

        question = self.current_question
        if selected_key not in question.choice_keys:
            raise ValueError("selected key is not one of the current choices")

        result = AnswerResult(
            is_correct=selected_key == question.answer.key,
            answer=question.answer,
            selected_key=selected_key,
        )
        self.current_result = result
        if result.is_correct:
            self.correct_count += 1
        return result

    def next_question(self) -> bool:
        """回答済みなら次へ進み、終了したかを返す。"""

        if self.is_finished:
            raise RuntimeError("quiz is already finished")
        if self.current_result is None:
            raise RuntimeError("answer the current question before continuing")

        self.current_index += 1
        self.current_result = None
        return self.is_finished


def create_quiz_session(
    kinoko: Sequence[Kinoko],
    question_count: int,
    rng: random.Random | None = None,
) -> QuizSession:
    """重複しない問題と、各問3択を作ってセッションを返す。"""

    if question_count not in QUESTION_COUNTS:
        raise ValueError("question count must be 5 or 10")
    if len(kinoko) < question_count:
        raise ValueError("not enough kinoko for the requested question count")
    if len(kinoko) < 3:
        raise ValueError("at least 3 kinoko are required")

    randomizer = rng or random.Random()
    answers = randomizer.sample(list(kinoko), question_count)
    questions: list[QuizQuestion] = []
    for answer in answers:
        distractor_pool = [item for item in kinoko if item.key != answer.key]
        choices = [answer, *randomizer.sample(distractor_pool, 2)]
        randomizer.shuffle(choices)
        questions.append(
            QuizQuestion(
                answer=answer,
                choices=(choices[0], choices[1], choices[2]),
            )
        )
    return QuizSession(questions=tuple(questions))
