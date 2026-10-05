"""Approved dinosaur search assets, separate from the existing quiz catalogue."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from data.subject_data import SubjectItem, load_ready_subject_items
from src.paths import PROJECT_ROOT


@dataclass(frozen=True)
class DinosaurSearchAssets:
    items: tuple[SubjectItem, ...]
    specimen_images: dict[str, Path]
    reconstruction_images: dict[str, Path]
    backgrounds: tuple[Path, ...]
    pending_reconstruction_keys: tuple[str, ...]

    @property
    def reconstruction_ready(self) -> bool:
        return not self.pending_reconstruction_keys


def _read(path: Path) -> dict:
    with path.open(encoding="utf-8") as source:
        return json.load(source)


def _png_path(directory: Path, filename: str) -> Path:
    if Path(filename).name != filename or not filename.endswith(".png"):
        raise ValueError("review image must be a local PNG filename")
    path = directory / filename
    if not path.is_file():
        raise ValueError(f"missing approved search image: {path}")
    return path


def _transparent_png(path: Path) -> Path:
    with Image.open(path) as image:
        if "A" not in image.getbands():
            raise ValueError(f"search cutout has no alpha channel: {path}")
        alpha = image.getchannel("A")
        histogram = alpha.histogram()
        total = image.width * image.height
        if histogram[0] / total < 0.05 or sum(histogram[245:]) / total < 0.02:
            raise ValueError(f"search cutout needs a transparent background and opaque subject: {path}")
    return path


def load_dinosaur_search_assets(root: Path = PROJECT_ROOT) -> DinosaurSearchAssets:
    """Use only approved images; never infer approval from a generated file."""
    review_dir = root / "assets/images/kyouryuu/review/transparent"
    old_review = _read(review_dir / "review-overrides.json")
    additions = _read(review_dir / "additions-review.json")
    background_dir = root / "assets/images/kyouryuu/review/search-backgrounds"
    background_review = _read(background_dir / "generation.json")
    if background_review.get("status") != "both_background_images_approved":
        raise ValueError("strata backgrounds need user approval")

    existing = load_ready_subject_items(root / "data/kyouryuu.json")
    existing_by_key = {item.key: item for item in existing}
    items: list[SubjectItem] = []
    specimens: dict[str, Path] = {}
    reconstructions: dict[str, Path] = {}
    for entry in old_review["items"]:
        if entry.get("image_status") != "approved":
            raise ValueError("existing specimen needs user approval")
        base = existing_by_key[entry["key"]]
        items.append(SubjectItem(base.key, base.name, "", ""))
        specimens[base.key] = _transparent_png(
            _png_path(review_dir, entry["review_image"])
        )
    if {item.key for item in items} != set(existing_by_key):
        raise ValueError("all existing dinosaurs must have approved specimens")
    for entry in additions["items"]:
        if entry.get("image_status") != "approved":
            raise ValueError("additional dinosaur images need user approval")
        key = entry["key"]
        if key in specimens:
            raise ValueError("duplicate dinosaur search key")
        # Search needs only the approved name, not undisplayed quiz hints.
        items.append(SubjectItem(key, entry["name"], "", ""))
        specimens[key] = _transparent_png(_png_path(review_dir, entry["specimen_image"]))
        reconstructions[key] = _transparent_png(
            _png_path(review_dir, entry["reconstruction_image"])
        )
    if len(items) != 18:
        raise ValueError("dinosaur search must include all 18 approved species")

    reconstruction_dir = review_dir / "reconstructions"
    reconstruction_record = reconstruction_dir / "review.json"
    if reconstruction_record.is_file():
        for entry in _read(reconstruction_record)["items"]:
            if entry.get("image_status") != "approved":
                continue
            key = entry["key"]
            if key not in existing_by_key:
                raise ValueError("unexpected reconstruction approval key")
            if key in reconstructions:
                raise ValueError("duplicate reconstruction approval key")
            reconstructions[key] = _transparent_png(
                _png_path(reconstruction_dir, entry["review_image"])
            )
    backgrounds = tuple(
        _png_path(background_dir, f"{entry['key']}.png")
        for entry in background_review["images"]
        if entry.get("image_status") == "approved"
    )
    if len(backgrounds) != 2:
        raise ValueError("fossil search needs exactly two approved backgrounds")
    return DinosaurSearchAssets(
        items=tuple(items),
        specimen_images=specimens,
        reconstruction_images=reconstructions,
        backgrounds=backgrounds,
        pending_reconstruction_keys=tuple(
            item.key for item in items if item.key not in reconstructions
        ),
    )
