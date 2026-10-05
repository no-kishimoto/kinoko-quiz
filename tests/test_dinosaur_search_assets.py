"""Approved search additions must not silently change the dinosaur quiz."""

import json
from pathlib import Path

import pytest
from PIL import Image

from src.dinosaur_search import _png_path, load_dinosaur_search_assets
from src.paths import KYOURYUU_DATA_PATH


def test_search_has_all_eighteen_approved_specimens_and_two_strata_backgrounds():
    assets = load_dinosaur_search_assets()
    assert len(assets.items) == len(assets.specimen_images) == 18
    assert len({item.key for item in assets.items}) == 18
    assert len(assets.backgrounds) == 2
    for path in assets.specimen_images.values():
        with Image.open(path) as image:
            assert image.getchannel("A").getextrema()[0] == 0


def test_unapproved_existing_reconstructions_are_not_used():
    assets = load_dinosaur_search_assets()
    assert not assets.reconstruction_ready
    assert len(assets.pending_reconstruction_keys) == 10
    assert len(assets.reconstruction_images) == 8
    assert not set(assets.pending_reconstruction_keys).intersection(assets.reconstruction_images)
    assert len(json.loads(KYOURYUU_DATA_PATH.read_text())) == 10


def test_image_references_cannot_escape_their_review_directory():
    with pytest.raises(ValueError, match="local PNG"):
        _png_path(Path("."), "../private.png")
