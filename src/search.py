"""森のなかのきのこを探すゲームの処理。"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw


@dataclass(frozen=True)
class SearchTarget:
    """探すきのこの名前と、背景画像上のあたり判定。"""

    key: str
    name: str
    x: float
    y: float
    radius: float

    def contains(self, x: float, y: float) -> bool:
        return (x - self.x) ** 2 + (y - self.y) ** 2 <= self.radius ** 2


TARGETS = (
    SearchTarget("kikurage", "きくらげ", 0.42, 0.31, 0.16),
    SearchTarget("benitengutake", "べにてんぐたけ", 0.22, 0.68, 0.13),
    SearchTarget("amigasatake", "あみがさたけ", 0.77, 0.58, 0.14),
)


@dataclass
class SearchSession:
    """見つけたきのこの状態。"""

    found_keys: set[str] = field(default_factory=set)

    @property
    def is_finished(self) -> bool:
        return len(self.found_keys) == len(TARGETS)

    @property
    def found_count(self) -> int:
        return len(self.found_keys)

    def find_at(self, x: float, y: float) -> SearchTarget | None:
        """正規化した座標で、まだ見つかっていないきのこを探す。"""

        for target in TARGETS:
            if target.key not in self.found_keys and target.contains(x, y):
                self.found_keys.add(target.key)
                return target
        return None


def targets_text(session: SearchSession) -> str:
    """画面に出す、探すきのこの一覧を作る。"""

    lines = ["### さがす きのこ"]
    for target in TARGETS:
        mark = "みつけた！" if target.key in session.found_keys else "まだだよ"
        lines.append(f"- {target.name}　{mark}")
    return "\n".join(lines)


def status_text(session: SearchSession, found: SearchTarget | None = None) -> str:
    """タップ後の短い案内を作る。"""

    if session.is_finished:
        return "## ぜんぶ みつけた！ きのこ さがし だいせいこう！"
    if found is not None:
        return f"## {found.name} を みつけた！\n\nあと {len(TARGETS) - session.found_count}こ だよ。"
    return f"## きのこを さがそう！\n\nあと {len(TARGETS) - session.found_count}こ だよ。"


def marked_scene(scene_path: str | Path, session: SearchSession) -> Image.Image:
    """見つけた場所だけに、やさしい丸いしるしを重ねる。"""

    with Image.open(scene_path) as opened:
        image = opened.convert("RGB")
    draw = ImageDraw.Draw(image)
    width, height = image.size
    for target in TARGETS:
        if target.key not in session.found_keys:
            continue
        x = target.x * width
        y = target.y * height
        radius = target.radius * min(width, height) * 0.72
        draw.ellipse(
            (x - radius, y - radius, x + radius, y + radius),
            outline=(255, 212, 59),
            width=max(6, int(min(width, height) * 0.008)),
        )
    return image
