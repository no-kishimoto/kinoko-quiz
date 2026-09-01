"""JSONで管理するきのこデータの読込と検証。"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

Toxicity = Literal["poisonous", "non_poisonous", "unknown"]
Edibility = Literal["edible", "not_edible", "unknown"]

_KEY_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
_KANJI_PATTERN = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")


class KinokoDataError(ValueError):
    """きのこデータが仕様を満たさない場合のエラー。"""


@dataclass(frozen=True)
class Highlight:
    """カラー表示する部位と、画像に対する円の比率。"""

    part: str
    x: float | None
    y: float | None
    radius: float | None

    @property
    def is_positioned(self) -> bool:
        """実画像に対する円の位置が設定済みかを返す。"""

        return self.x is not None and self.y is not None and self.radius is not None


@dataclass(frozen=True)
class Kinoko:
    """ゲームと図鑑で使用する1種類分のきのこ情報。"""

    key: str
    name: str
    habitat: str
    season: str
    size: str
    color: str
    features: str
    quiz_hint: str
    toxicity: Toxicity
    edibility: Edibility
    caution: str
    similar_kinoko: str
    cooking: str | None
    trivia: str
    highlight: Highlight

    @property
    def image_filename(self) -> str:
        """管理用キーから対応する画像ファイル名を返す。"""

        return f"{self.key}.png"


_TEXT_FIELDS = (
    "name", "habitat", "season", "size", "color", "features",
    "quiz_hint", "caution", "similar_kinoko", "trivia",
)


def _required_text(raw: dict[str, Any], field: str, index: int) -> str:
    value = raw.get(field)
    if not isinstance(value, str) or not value.strip():
        raise KinokoDataError(f"entry {index}: {field} must be a non-empty string")
    if _KANJI_PATTERN.search(value):
        raise KinokoDataError(f"entry {index}: {field} must not contain kanji")
    return value.strip()


def _parse_highlight(raw: Any, index: int) -> Highlight:
    if not isinstance(raw, dict):
        raise KinokoDataError(f"entry {index}: highlight must be an object")
    part = raw.get("part")
    if not isinstance(part, str) or not part.strip():
        raise KinokoDataError(f"entry {index}: highlight.part must be a non-empty string")
    if _KANJI_PATTERN.search(part):
        raise KinokoDataError(f"entry {index}: highlight.part must not contain kanji")

    raw_values = [raw.get(field) for field in ("x", "y", "radius")]
    if all(value is None for value in raw_values):
        return Highlight(part=part.strip(), x=None, y=None, radius=None)
    if any(value is None for value in raw_values):
        raise KinokoDataError(
            f"entry {index}: highlight x, y, and radius must all be set or all be null"
        )

    values: dict[str, float] = {}
    for field in ("x", "y", "radius"):
        value = raw.get(field)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise KinokoDataError(f"entry {index}: highlight.{field} must be a number")
        values[field] = float(value)
    if not 0.0 <= values["x"] <= 1.0 or not 0.0 <= values["y"] <= 1.0:
        raise KinokoDataError(f"entry {index}: highlight x and y must be between 0 and 1")
    if not 0.0 < values["radius"] <= 0.5:
        raise KinokoDataError(
            f"entry {index}: highlight radius must be greater than 0 and at most 0.5"
        )
    return Highlight(part=part.strip(), **values)


def _parse_kinoko(raw: Any, index: int) -> Kinoko:
    if not isinstance(raw, dict):
        raise KinokoDataError(f"entry {index}: each item must be an object")
    key = raw.get("key")
    if not isinstance(key, str) or not _KEY_PATTERN.fullmatch(key):
        raise KinokoDataError(
            f"entry {index}: key must use lowercase letters, numbers, and underscores"
        )
    text = {field: _required_text(raw, field, index) for field in _TEXT_FIELDS}
    toxicity = raw.get("toxicity")
    if toxicity not in ("poisonous", "non_poisonous", "unknown"):
        raise KinokoDataError(
            f"entry {index}: toxicity must be poisonous, non_poisonous, or unknown"
        )
    edibility = raw.get("edibility")
    if edibility not in ("edible", "not_edible", "unknown"):
        raise KinokoDataError(
            f"entry {index}: edibility must be edible, not_edible, or unknown"
        )
    cooking = raw.get("cooking")
    if cooking is not None:
        if not isinstance(cooking, str) or not cooking.strip():
            raise KinokoDataError(f"entry {index}: cooking must be null or a non-empty string")
        if _KANJI_PATTERN.search(cooking):
            raise KinokoDataError(f"entry {index}: cooking must not contain kanji")
        cooking = cooking.strip()
    if edibility == "edible" and cooking is None:
        raise KinokoDataError(f"entry {index}: edible mushrooms require cooking")
    if edibility != "edible" and cooking is not None:
        raise KinokoDataError(f"entry {index}: only edible mushrooms may define cooking")
    return Kinoko(
        key=key,
        toxicity=toxicity,
        edibility=edibility,
        cooking=cooking,
        highlight=_parse_highlight(raw.get("highlight"), index),
        **text,
    )


def load_kinoko(path: str | Path) -> tuple[Kinoko, ...]:
    """JSONファイルを読み込み、検証済みデータを返す。"""

    data_path = Path(path)
    try:
        raw = json.loads(data_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise KinokoDataError(f"could not read kinoko data: {data_path}") from exc
    if not isinstance(raw, list):
        raise KinokoDataError("kinoko data root must be an array")
    kinoko = tuple(_parse_kinoko(item, index) for index, item in enumerate(raw))
    keys = [item.key for item in kinoko]
    if len(keys) != len(set(keys)):
        raise KinokoDataError("kinoko keys must be unique")
    names = [item.name for item in kinoko]
    if len(names) != len(set(names)):
        raise KinokoDataError("kinoko names must be unique")
    return kinoko


def validate_image_assets(kinoko: tuple[Kinoko, ...], image_dir: str | Path) -> None:
    """全データの円位置と対応するPNG画像を検証する。"""

    directory = Path(image_dir)
    unpositioned = [item.key for item in kinoko if not item.highlight.is_positioned]
    if unpositioned:
        raise KinokoDataError(
            f"highlight positions are not set: {', '.join(unpositioned)}"
        )
    missing = [
        item.image_filename
        for item in kinoko
        if not (directory / item.image_filename).is_file()
    ]
    if missing:
        raise KinokoDataError(f"missing image assets: {', '.join(missing)}")
