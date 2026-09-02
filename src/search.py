"""森のなかのきのこを探すゲームの処理。"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from PIL import Image, ImageDraw


@dataclass(frozen=True)
class SearchTarget:
    key: str
    name: str
    x: float
    y: float
    radius: float

    def contains(self, x: float, y: float) -> bool:
        return (x - self.x) ** 2 + (y - self.y) ** 2 <= self.radius ** 2


@dataclass(frozen=True)
class SearchQuestion:
    key: str
    targets: tuple[SearchTarget, SearchTarget, SearchTarget]

    @property
    def image_filename(self) -> str:
        return f"{self.key}.png"


_NAMES = {
    "benitengutake": "べにてんぐたけ", "dokutsurutake": "どくつるたけ",
    "tsukiyotake": "つきよたけ", "rappatake": "らっぱたけ",
    "matsutake": "まつたけ", "hiratake": "ひらたけ",
    "kikurage": "きくらげ", "amigasatake": "あみがさたけ",
    "suppontake": "すっぽんたけ",
}
_LAYOUTS = (
    ((0.19, 0.70, 0.12), (0.51, 0.44, 0.13), (0.81, 0.65, 0.12)),
    ((0.25, 0.48, 0.12), (0.68, 0.33, 0.12), (0.74, 0.77, 0.13)),
    ((0.17, 0.76, 0.12), (0.46, 0.28, 0.12), (0.84, 0.56, 0.13)),
    ((0.29, 0.62, 0.12), (0.57, 0.73, 0.13), (0.78, 0.39, 0.12)),
    ((0.18, 0.42, 0.12), (0.49, 0.61, 0.13), (0.82, 0.73, 0.12)),
)
_KINDS = (
    ("benitengutake", "amigasatake", "kikurage"),
    ("matsutake", "hiratake", "suppontake"),
    ("dokutsurutake", "rappatake", "kikurage"),
    ("tsukiyotake", "amigasatake", "matsutake"),
    ("hiratake", "benitengutake", "rappatake"),
    ("suppontake", "kikurage", "dokutsurutake"),
    ("amigasatake", "tsukiyotake", "hiratake"),
    ("matsutake", "rappatake", "benitengutake"),
    ("kikurage", "suppontake", "amigasatake"),
    ("dokutsurutake", "hiratake", "matsutake"),
    ("tsukiyotake", "rappatake", "kikurage"),
    ("benitengutake", "suppontake", "hiratake"),
    ("amigasatake", "dokutsurutake", "matsutake"),
    ("rappatake", "kikurage", "benitengutake"),
    ("suppontake", "tsukiyotake", "amigasatake"),
)


def _question(index: int, kinds: tuple[str, str, str]) -> SearchQuestion:
    layout = _LAYOUTS[index % len(_LAYOUTS)]
    targets = tuple(SearchTarget(key, _NAMES[key], *position) for key, position in zip(kinds, layout))
    return SearchQuestion(key=f"forest_{index + 1:02d}", targets=targets)  # type: ignore[arg-type]


SEARCH_QUESTIONS = tuple(_question(index, kinds) for index, kinds in enumerate(_KINDS))


@dataclass
class SearchSession:
    question: SearchQuestion
    found_keys: set[str] = field(default_factory=set)

    @property
    def is_finished(self) -> bool:
        return len(self.found_keys) == len(self.question.targets)

    @property
    def found_count(self) -> int:
        return len(self.found_keys)

    def find_at(self, x: float, y: float) -> SearchTarget | None:
        for target in self.question.targets:
            if target.key not in self.found_keys and target.contains(x, y):
                self.found_keys.add(target.key)
                return target
        return None


def create_search_session(questions: Sequence[SearchQuestion] = SEARCH_QUESTIONS, rng: random.Random | None = None) -> SearchSession:
    if not questions:
        raise ValueError("at least one search question is required")
    return SearchSession(question=(rng or random.Random()).choice(tuple(questions)))


def targets_text(session: SearchSession) -> str:
    lines = ["### さがす きのこ"]
    for target in session.question.targets:
        mark = "みつけた！" if target.key in session.found_keys else "まだだよ"
        lines.append(f"- {target.name}　{mark}")
    return "\n".join(lines)


def status_text(session: SearchSession, found: SearchTarget | None = None) -> str:
    if session.is_finished:
        return "## ぜんぶ みつけた！ きのこ さがし だいせいこう！"
    remaining = len(session.question.targets) - session.found_count
    if found is not None:
        return f"## {found.name} を みつけた！\n\nあと {remaining}こ だよ。"
    return f"## きのこを さがそう！\n\nあと {remaining}こ だよ。"


def marked_scene(scene_path: str | Path, session: SearchSession) -> Image.Image:
    with Image.open(scene_path) as opened:
        image = opened.convert("RGB")
    draw = ImageDraw.Draw(image)
    width, height = image.size
    for target in session.question.targets:
        if target.key not in session.found_keys:
            continue
        x, y = target.x * width, target.y * height
        radius = target.radius * min(width, height) * 0.72
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), outline=(255, 212, 59), width=max(6, int(min(width, height) * 0.008)))
    return image
