"""Approved strata assets support fossil search without changing forest assets."""

import json
import re
from html.parser import HTMLParser
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
REVIEW_DIR = ROOT / "assets/images/kyouryuu/review/search-backgrounds"


def test_two_approved_opaque_landscape_backgrounds_are_used_for_fossil_search():
    generation = json.loads((REVIEW_DIR / "generation.json").read_text())
    assert generation["status"] == "both_background_images_approved"
    assert generation["approval_date"] == "2026-10-05"
    assert "Gradio fossil search" in generation["game_integration"]
    assert generation["approved_design"]["background_count"] == 2
    assert len(generation["images"]) == 2
    assert {item["key"] for item in generation["images"]} == {
        "strata-sandstone-v1", "strata-limestone-v1",
    }
    for item in generation["images"]:
        assert item["image_status"] == "approved"
        assert item["image_approval_date"] == generation["approval_date"]
        assert item["prompt"]
        assert item["generated_path"]
        with Image.open(REVIEW_DIR / f"{item['key']}.png") as image:
            assert image.format == "PNG"
            assert image.width >= 1024 and image.width > image.height
            assert image.width * 3 == image.height * 4
            assert image.convert("RGBA").getchannel("A").getextrema() == (255, 255)


class ReviewReferences(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []
        self.links = []
        self.text = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "img":
            self.images.append(attributes["src"])
        if tag == "a":
            self.links.append(attributes["href"])

    def handle_data(self, data):
        self.text.append(data)


def test_review_page_references_existing_backgrounds_and_specimen_examples():
    page = ReviewReferences()
    page.feed((REVIEW_DIR / "index.html").read_text())
    assert len(page.images) == 8
    for reference in page.images + page.links:
        assert (REVIEW_DIR / reference).is_file()
    assert not re.search(r"[\u3400-\u4dbf\u4e00-\u9fff]", "".join(page.text))


def test_review_assets_do_not_become_live_search_backgrounds():
    live_backgrounds = ROOT / "assets/images/search/backgrounds"
    assert {path.name for path in live_backgrounds.glob("*.png")} == {
        "roots.png", "stream.png", "autumn_log.png", "rain_moss.png",
    }
