"""All eighteen species keep their independent search-image approvals."""

import json
from pathlib import Path

import pytest
from PIL import Image

from src.dinosaur_search import _png_path, load_dinosaur_search_assets
from data.subject_data import load_ready_subject_items
from src.paths import KYOURYUU_DATA_PATH


def test_search_has_all_eighteen_approved_specimens_and_two_strata_backgrounds():
    assets = load_dinosaur_search_assets()
    assert len(assets.items) == len(assets.specimen_images) == 18
    assert len({item.key for item in assets.items}) == 18
    assert len(assets.backgrounds) == 2
    for path in assets.specimen_images.values():
        with Image.open(path) as image:
            assert image.getchannel("A").getextrema()[0] == 0


def test_unapproved_existing_reconstructions_are_not_used(monkeypatch):
    from src import dinosaur_search
    read = dinosaur_search._read

    def pending_review(path):
        record = read(path)
        if path.name == "review.json" and path.parent.name == "reconstructions":
            for entry in record["items"]:
                entry["image_status"] = "awaiting_user_review"
        return record

    monkeypatch.setattr(dinosaur_search, "_read", pending_review)
    assets = load_dinosaur_search_assets()
    assert not assets.reconstruction_ready
    assert len(assets.pending_reconstruction_keys) == 10
    assert len(assets.reconstruction_images) == 8
    assert not set(assets.pending_reconstruction_keys).intersection(assets.reconstruction_images)
    assert len(json.loads(KYOURYUU_DATA_PATH.read_text())) == 18


def test_search_covers_the_eighteen_species_in_the_expanded_quiz_catalogue():
    assets = load_dinosaur_search_assets()
    catalogue = load_ready_subject_items(KYOURYUU_DATA_PATH)
    assert len(catalogue) == 18
    assert {item.key for item in catalogue} == {item.key for item in assets.items}


@pytest.mark.parametrize(
    ("record_name", "message"),
    [
        ("review-overrides.json", "existing specimen needs user approval"),
        ("additions-review.json", "additional dinosaur images need user approval"),
    ],
)
def test_unapproved_specimens_are_rejected_after_quiz_expansion(monkeypatch, record_name, message):
    from src import dinosaur_search
    read = dinosaur_search._read

    def pending_review(path):
        record = read(path)
        if path.name == record_name:
            record["items"][0]["image_status"] = "awaiting_user_review"
        return record

    monkeypatch.setattr(dinosaur_search, "_read", pending_review)
    with pytest.raises(ValueError, match=message):
        load_dinosaur_search_assets()


@pytest.mark.parametrize("record_name", ["review-overrides.json", "additions-review.json"])
def test_duplicate_approved_specimens_are_rejected(monkeypatch, record_name):
    from src import dinosaur_search
    read = dinosaur_search._read

    def duplicate_review(path):
        record = read(path)
        if path.name == record_name:
            record["items"].append(dict(record["items"][0]))
        return record

    monkeypatch.setattr(dinosaur_search, "_read", duplicate_review)
    with pytest.raises(ValueError, match="duplicate dinosaur search key"):
        load_dinosaur_search_assets()


def test_missing_original_specimen_approval_is_rejected(monkeypatch):
    from src import dinosaur_search
    read = dinosaur_search._read

    def incomplete_review(path):
        record = read(path)
        if path.name == "review-overrides.json":
            record["items"].pop()
        return record

    monkeypatch.setattr(dinosaur_search, "_read", incomplete_review)
    with pytest.raises(ValueError, match="all existing dinosaurs must have approved specimens"):
        load_dinosaur_search_assets()


def test_original_and_additional_approval_keys_cannot_overlap(monkeypatch):
    from src import dinosaur_search
    read = dinosaur_search._read

    def overlapping_review(path):
        record = read(path)
        if path.name == "additions-review.json":
            record["items"][0]["key"] = "tyrannosaurus"
        return record

    monkeypatch.setattr(dinosaur_search, "_read", overlapping_review)
    with pytest.raises(ValueError, match="duplicate dinosaur search key"):
        load_dinosaur_search_assets()


def test_image_references_cannot_escape_their_review_directory():
    with pytest.raises(ValueError, match="local PNG"):
        _png_path(Path("."), "../private.png")


def test_approved_living_catalog_is_complete_and_ready():
    assets = load_dinosaur_search_assets()
    assert assets.reconstruction_ready
    assert assets.pending_reconstruction_keys == ()
    assert len(assets.reconstruction_images) == 18
    assert set(assets.reconstruction_images) == {item.key for item in assets.items}
    for path in assets.reconstruction_images.values():
        with Image.open(path) as image:
            assert image.getchannel("A").getextrema()[0] == 0
