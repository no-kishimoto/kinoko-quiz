"""指定されたなかまを、森や地層のなかから探すゲーム。"""

from __future__ import annotations

import random
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from itertools import combinations
from math import hypot
from pathlib import Path

from PIL import Image, ImageDraw

from data.kinoko_data import Kinoko
from data.subject_data import SubjectItem

QUESTION_COUNT = 5
SearchItem = Kinoko | SubjectItem
_DINOSAUR_MODES = frozenset(("fossil", "reconstruction"))


@dataclass(frozen=True)
class SearchPlacement:
    item: SearchItem
    x: float
    y: float
    # 見た目より少し広い当たり判定。小さい画像でも遊びやすくする。
    radius: float = 0.11

    def contains(self, x: float, y: float) -> bool:
        return (x - self.x) ** 2 + (y - self.y) ** 2 <= self.radius ** 2


@dataclass
class SearchSession:
    background_path: Path
    target: SearchPlacement
    decoys: tuple[SearchPlacement, SearchPlacement]
    current_index: int = 0
    correct_count: int = 0
    is_correct: bool = False
    mode: str = "default"
    habitat: str | None = None
    used_target_keys: tuple[str, ...] = ()

    @property
    def total_questions(self) -> int:
        return QUESTION_COUNT

    @property
    def progress_text(self) -> str:
        return f"もんだい {self.current_index + 1} / {self.total_questions}"

    @property
    def is_last_question(self) -> bool:
        return self.current_index + 1 >= self.total_questions

    @property
    def placements(self) -> tuple[SearchPlacement, SearchPlacement, SearchPlacement]:
        return (self.target, *self.decoys)

    def choose_at(self, x: float, y: float) -> bool:
        if self.is_correct:
            return False
        if self.target.contains(x, y):
            self.is_correct = True
            self.correct_count += 1
            return True
        return False


_POSITIONS = (
    (0.16, 0.72), (0.28, 0.48), (0.44, 0.34), (0.53, 0.66),
    (0.66, 0.42), (0.80, 0.70), (0.83, 0.30), (0.34, 0.78),
)
_DINOSAUR_POSITIONS = (
    (0.20, 0.28), (0.50, 0.28), (0.80, 0.28),
    (0.20, 0.72), (0.50, 0.72), (0.80, 0.72),
)


def _choose_positions(
    randomizer: random.Random,
    positions: Sequence[tuple[float, float]],
    radius: float,
) -> list[tuple[float, float]]:
    """クリック範囲が重ならない場所を3つ選ぶ。"""

    choices = [
        group
        for group in combinations(positions, 3)
        if all(
            hypot(ax - bx, ay - by) > 2 * radius
            for (ax, ay), (bx, by) in combinations(group, 2)
        )
    ]
    return randomizer.sample(randomizer.choice(choices), 3)


def create_search_session(
    kinoko: Sequence[SearchItem],
    backgrounds: Sequence[Path],
    rng: random.Random | None = None,
    current_index: int = 0,
    correct_count: int = 0,
    *,
    mode: str = "default",
    used_target_keys: Sequence[str] = (),
    unique_targets: bool = False,
    habitats: Mapping[str, str] | None = None,
    habitat_backgrounds: Mapping[str, Sequence[Path]] | None = None,
) -> SearchSession:
    """1種類を指定し、異なる2種類をまぎれこませる。"""

    items = list({item.key: item for item in kinoko}.values())
    if len(items) < 3:
        raise ValueError("at least three distinct items are required")
    if not backgrounds:
        raise ValueError("at least one search background is required")
    randomizer = rng or random.Random()
    history = tuple(used_target_keys)
    eligible = [item for item in items if not unique_targets or item.key not in history]
    if not eligible:
        raise ValueError("no unused search targets remain")
    if (habitats is None) != (habitat_backgrounds is None):
        raise ValueError("habitats and habitat backgrounds must be supplied together")
    target_item = randomizer.choice(eligible)
    habitat = habitats[target_item.key] if habitats is not None else None
    decoy_items = [
        item for item in items
        if item.key != target_item.key and (habitats is None or habitats[item.key] == habitat)
    ]
    if len(decoy_items) < 2:
        raise ValueError("each search habitat needs at least three species")
    chosen = [target_item, *randomizer.sample(decoy_items, 2)]
    matching_backgrounds = habitat_backgrounds[habitat] if habitat_backgrounds is not None else backgrounds
    if not matching_backgrounds:
        raise ValueError("search habitat needs a matching background")
    radius = 0.14 if mode in _DINOSAUR_MODES else 0.11
    available_positions = _DINOSAUR_POSITIONS if mode in _DINOSAUR_MODES else _POSITIONS
    if habitat == "land":
        available_positions = tuple((x, y) for y in (0.53, 0.82) for x in (0.20, 0.50, 0.80))
    positions = _choose_positions(randomizer, available_positions, radius)
    target = SearchPlacement(chosen[0], *positions[0], radius=radius)
    decoys = (
        SearchPlacement(chosen[1], *positions[1], radius=radius),
        SearchPlacement(chosen[2], *positions[2], radius=radius),
    )
    return SearchSession(
        background_path=randomizer.choice(list(matching_backgrounds)),
        habitat=habitat,
        target=target,
        decoys=decoys,
        current_index=current_index,
        correct_count=correct_count,
        mode=mode,
        used_target_keys=(*history, target.item.key),
    )


def prompt_text(session: SearchSession) -> str:
    return f"# {session.target.item.name} を さがせ！"


def status_text(session: SearchSession, clicked: bool = False) -> str:
    if session.is_correct:
        return f"## せいかい！ {session.target.item.name} を みつけた！"
    if clicked:
        return "## おしい！ もういちど さがしてみよう。"
    if session.mode == "fossil":
        return "## ちそうの なかを クリックしてね。"
    if session.habitat is not None:
        label = {"ancient_forest": "こだいの もり", "ancient_plain": "こだいの へいげん", "primeval_sea": "たいこの うみ"}[session.background_path.stem]
        return f"## {label}を クリックしてね。"
    return "## もりの なかを クリックしてね。"


def _sprite(image_path: Path, size: int, *, preserve_colors: bool = False) -> Image.Image:
    with Image.open(image_path) as opened:
        sprite = opened.convert("RGBA")
    if not preserve_colors:
        # 以前のきのこ・なかま画像にある青い背景だけを抜く。
        pixels = sprite.load()
        for y in range(sprite.height):
            for x in range(sprite.width):
                red, green, blue, alpha = pixels[x, y]
                if blue > 145 and green > 110 and red < 130 and blue > red + 40:
                    pixels[x, y] = (red, green, blue, 0)
        box = sprite.getbbox()
        if box:
            sprite = sprite.crop(box)
    sprite.thumbnail((size, size), Image.Resampling.LANCZOS)
    return sprite


def render_scene(
    session: SearchSession, zukan_image_dir: Path | Mapping[str, Path],
) -> Image.Image:
    """画像フォルダまたは種類ごとの画像パスから、問題画像を作る。"""

    with Image.open(session.background_path) as opened:
        image = opened.convert("RGBA")
    width, height = image.size
    dinosaur_mode = session.mode in _DINOSAUR_MODES
    # 正方形の画像でも四隅までクリック範囲に入り、画面内へ収まる大きさ。
    sprite_size = max(1, int(min(width, height) * (0.19 if dinosaur_mode else 0.18)))
    target_bounds: tuple[int, int, int, int] | None = None
    for placement in session.placements:
        image_path = (
            zukan_image_dir[placement.item.key]
            if isinstance(zukan_image_dir, Mapping)
            else zukan_image_dir / placement.item.image_filename
        )
        sprite = _sprite(image_path, sprite_size, preserve_colors=dinosaur_mode)
        x = int(placement.x * width) - sprite.width // 2
        y = (
            int(placement.y * height) - sprite.height // 2
            if dinosaur_mode
            else int((placement.y + placement.radius * 0.55) * height) - sprite.height
        )
        image.alpha_composite(sprite, (x, y))
        if placement is session.target:
            target_bounds = (x, y, x + sprite.width, y + sprite.height)
    if session.is_correct:
        draw = ImageDraw.Draw(image)
        x, y = session.target.x * width, session.target.y * height
        stroke_width = max(1 if dinosaur_mode else 6, int(min(width, height) * 0.008))
        if dinosaur_mode and target_bounds is not None:
            left, top, right, bottom = target_bounds
            x, y = (left + right) / 2, (top + bottom) / 2
            radius = (
                hypot(right - left, bottom - top) / 2
                + stroke_width + min(width, height) * 0.01
            )
        else:
            radius = session.target.radius * min(width, height) * 1.25
        draw.ellipse(
            (x - radius, y - radius, x + radius, y + radius),
            outline=(255, 212, 59), width=stroke_width,
        )
    return image.convert("RGB")
