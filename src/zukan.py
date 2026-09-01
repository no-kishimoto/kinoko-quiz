"""きのこ図鑑のページ分けと詳細表示用の処理。"""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Sequence

from data.kinoko_data import Kinoko

PAGE_SIZE = 3


@dataclass(frozen=True)
class ZukanPage:
    """図鑑一覧の1ページ分。"""

    index: int
    total_pages: int
    items: tuple[Kinoko, ...]

    @property
    def page_text(self) -> str:
        return f"{self.index + 1} / {self.total_pages}"

    @property
    def has_previous(self) -> bool:
        return self.index > 0

    @property
    def has_next(self) -> bool:
        return self.index < self.total_pages - 1


def page_count(kinoko: Sequence[Kinoko], page_size: int = PAGE_SIZE) -> int:
    """登録数から必要な図鑑ページ数を返す。"""

    if page_size < 1:
        raise ValueError("page size must be at least 1")
    return ceil(len(kinoko) / page_size)


def zukan_page(
    kinoko: Sequence[Kinoko],
    index: int,
    page_size: int = PAGE_SIZE,
) -> ZukanPage:
    """指定ページの最大3種類を返す。"""

    total_pages = page_count(kinoko, page_size)
    if total_pages == 0:
        raise ValueError("at least one kinoko is required")
    bounded_index = min(max(index, 0), total_pages - 1)
    start = bounded_index * page_size
    return ZukanPage(
        index=bounded_index,
        total_pages=total_pages,
        items=tuple(kinoko[start:start + page_size]),
    )


def zukan_detail_text(item: Kinoko, toxicity_label: str) -> str:
    """図鑑詳細で見せる、子ども向けの説明を作る。"""

    sections = [
        f"### はえる ばしょ\n{item.habitat}",
        f"### でる きせつ\n{item.season}",
        f"### おおきさ\n{item.size}",
        f"### いろ\n{item.color}",
        f"### とくちょう\n{item.features}",
        f"### {toxicity_label}\n{item.caution}",
        f"### にている きのこ\n{item.similar_kinoko}",
    ]
    if item.cooking is not None:
        sections.append(f"### たべかた\n{item.cooking}")
    sections.append(f"### まめちしき\n{item.trivia}")
    return "\n\n".join(sections)
