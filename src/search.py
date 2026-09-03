"""指定されたきのこを森のなかから探すゲーム。"""

from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from PIL import Image, ImageDraw

from data.kinoko_data import Kinoko


@dataclass(frozen=True)
class SearchPlacement:
    item: Kinoko
    x: float
    y: float
    # 見た目より少し広い当たり判定。小さいきのこでも遊びやすくする。
    radius: float = 0.11

    def contains(self, x: float, y: float) -> bool:
        return (x - self.x) ** 2 + (y - self.y) ** 2 <= self.radius ** 2


@dataclass
class SearchSession:
    background_path: Path
    target: SearchPlacement
    decoys: tuple[SearchPlacement, SearchPlacement]
    is_correct: bool = False

    @property
    def placements(self) -> tuple[SearchPlacement, SearchPlacement, SearchPlacement]:
        return (self.target, *self.decoys)

    def choose_at(self, x: float, y: float) -> bool:
        if self.is_correct:
            return False
        if self.target.contains(x, y):
            self.is_correct = True
            return True
        return False


_POSITIONS = (
    (0.16, 0.72), (0.28, 0.48), (0.44, 0.34), (0.53, 0.66),
    (0.66, 0.42), (0.80, 0.70), (0.83, 0.30), (0.34, 0.78),
)


def create_search_session(
    kinoko: Sequence[Kinoko],
    backgrounds: Sequence[Path],
    rng: random.Random | None = None,
) -> SearchSession:
    """30種類から1つを指定し、ほか2つをまぎれこませる。"""

    if len(kinoko) < 3:
        raise ValueError("at least three mushrooms are required")
    if not backgrounds:
        raise ValueError("at least one forest background is required")
    randomizer = rng or random.Random()
    chosen = randomizer.sample(list(kinoko), 3)
    positions = randomizer.sample(_POSITIONS, 3)
    target = SearchPlacement(chosen[0], *positions[0])
    decoys = (
        SearchPlacement(chosen[1], *positions[1]),
        SearchPlacement(chosen[2], *positions[2]),
    )
    return SearchSession(background_path=randomizer.choice(list(backgrounds)), target=target, decoys=decoys)


def prompt_text(session: SearchSession) -> str:
    return f"# {session.target.item.name} を さがせ！"


def status_text(session: SearchSession, clicked: bool = False) -> str:
    if session.is_correct:
        return f"## せいかい！ {session.target.item.name} を みつけた！"
    if clicked:
        return "## おしい！ もういちど さがしてみよう。"
    return "## もりの なかを クリックしてね。"


def _sprite(image_path: Path, size: int) -> Image.Image:
    with Image.open(image_path) as opened:
        sprite = opened.convert("RGBA")
    # 青い背景で作った新しい図鑑絵も、森の上にきれいに重ねる。
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


def render_scene(session: SearchSession, zukan_image_dir: Path) -> Image.Image:
    """背景へ、小さなきのこ3つを重ねた問題画像を作る。"""

    with Image.open(session.background_path) as opened:
        image = opened.convert("RGBA")
    width, height = image.size
    for placement in session.placements:
        sprite = _sprite(zukan_image_dir / placement.item.image_filename, int(min(width, height) * 0.18))
        x = int(placement.x * width) - sprite.width // 2
        y = int((placement.y + placement.radius * 0.55) * height) - sprite.height
        image.alpha_composite(sprite, (x, y))
    if session.is_correct:
        draw = ImageDraw.Draw(image)
        x, y = session.target.x * width, session.target.y * height
        radius = session.target.radius * min(width, height) * 1.25
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), outline=(255, 212, 59), width=max(6, int(min(width, height) * 0.008)))
    return image.convert("RGB")
