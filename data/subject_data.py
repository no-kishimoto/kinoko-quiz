"""しょくぶつとこんちゅうの、これからのゲーム用のなまえデータ。"""

from __future__ import annotations

import json
import re
from pathlib import Path


_KEY = re.compile(r"^[a-z][a-z0-9_]*$")
_KANJI = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")


class SubjectDataError(ValueError):
    """なかまデータがこわれているときのエラー。"""


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
