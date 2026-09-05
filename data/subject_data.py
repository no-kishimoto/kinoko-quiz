"""しょくぶつとこんちゅうの、これからのゲーム用のなまえデータ。"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path


_KEY = re.compile(r"^[a-z][a-z0-9_]*$")
_KANJI = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")


class SubjectDataError(ValueError):
    """なかまデータがこわれているときのエラー。"""


@dataclass(frozen=True)
class SubjectItem:
    """きのこ以外のクイズとずかんで使う、1種類分のデータ。"""

    key: str
    name: str
    quiz_hint: str
    zukan_text: str

    @property
    def image_filename(self) -> str:
        return f"{self.key}.png"


def load_subject_names(path: str | Path) -> tuple[str, ...]:
    """キーとなまえだけのデータを、表示用のなまえとして読み込む。"""

    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SubjectDataError(f"could not read subject data: {path}") from exc
    if not isinstance(raw, list):
        raise SubjectDataError("subject data root must be an array")

    keys: list[str] = []
    names: list[str] = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise SubjectDataError(f"entry {index}: item must be an object")
        key, name = item.get("key"), item.get("name")
        if not isinstance(key, str) or not _KEY.fullmatch(key):
            raise SubjectDataError(f"entry {index}: invalid key")
        if not isinstance(name, str) or not name.strip() or _KANJI.search(name):
            raise SubjectDataError(f"entry {index}: invalid name")
        keys.append(key)
        names.append(name.strip())
    if len(keys) != len(set(keys)) or len(names) != len(set(names)):
        raise SubjectDataError("keys and names must be unique")
    return tuple(names)


def load_ready_subject_items(path: str | Path) -> tuple[SubjectItem, ...]:
    """説明とヒントがそろった種類だけを、ゲーム用に読み込む。"""

    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SubjectDataError(f"could not read subject data: {path}") from exc
    if not isinstance(raw, list):
        raise SubjectDataError("subject data root must be an array")

    items: list[SubjectItem] = []
    for index, entry in enumerate(raw):
        if not isinstance(entry, dict):
            raise SubjectDataError(f"entry {index}: item must be an object")
        key, name = entry.get("key"), entry.get("name")
        if not isinstance(key, str) or not _KEY.fullmatch(key):
            raise SubjectDataError(f"entry {index}: invalid key")
        if not isinstance(name, str) or not name.strip() or _KANJI.search(name):
            raise SubjectDataError(f"entry {index}: invalid name")
        quiz_hint, zukan_text = entry.get("quiz_hint"), entry.get("zukan_text")
        if quiz_hint is None and zukan_text is None:
            continue
        if not isinstance(quiz_hint, str) or not quiz_hint.strip() or _KANJI.search(quiz_hint):
            raise SubjectDataError(f"entry {index}: invalid quiz_hint")
        if not isinstance(zukan_text, str) or not zukan_text.strip() or _KANJI.search(zukan_text):
            raise SubjectDataError(f"entry {index}: invalid zukan_text")
        items.append(SubjectItem(key, name.strip(), quiz_hint.strip(), zukan_text.strip()))
    if len({item.key for item in items}) != len(items):
        raise SubjectDataError("ready item keys must be unique")
    return tuple(items)
