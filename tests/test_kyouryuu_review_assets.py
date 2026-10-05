"""Approved search assets must not silently expand the quiz catalogue."""

import json
import re
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
REVIEW_DIR = ROOT / "assets/images/kyouryuu/review/transparent"
EXPECTED = {
    "coelacanth", "ankylosaurus", "parasaurolophus", "trilobite",
    "anomalocaris", "ottoia", "mammoth", "smilodon",
}


def test_additions_review_contains_eight_description_and_image_pairs():
    review = json.loads((REVIEW_DIR / "additions-review.json").read_text())
    candidates = json.loads((ROOT / "data/kyouryuu_candidates.json").read_text())
    original_text = {item["key"]: item["zukan_text"] for item in candidates}
    assert review["status"] == "all_8_images_and_descriptions_approved"
    assert review["approval_date"] == "2026-10-05"
    assert review["approved_fields"] == [
        "zukan_text", "specimen_image", "reconstruction_image",
    ]
    assert "Gradio fossil search" in review["game_integration"]
    assert "Quiz and encyclopedia are unchanged" in review["game_integration"]
    assert len(review["items"]) == 8
    assert {item["key"] for item in review["items"]} == EXPECTED
    for item in review["items"]:
        assert item["zukan_text"] == original_text[item["key"]]
        assert not re.search(r"[\u3400-\u4dbf\u4e00-\u9fff]", item["name"] + item["zukan_text"])
        assert item["description_status"] == "approved"
        assert item["image_status"] == "approved"
        assert item["image_approval_date"] == review["approval_date"]
        assert item["source_urls"]
        for field in ("specimen_image", "reconstruction_image"):
            with Image.open(REVIEW_DIR / item[field]) as image:
                assert image.format == "PNG"
                assert "A" in image.getbands()
                alpha = image.getchannel("A")
                histogram = alpha.histogram()
                total = image.width * image.height
                assert histogram[0] / total > 0.1, "Background must be genuinely transparent"
                assert sum(histogram[245:]) / total > 0.05, "Subject must not be a translucent ghost"


def test_review_does_not_add_unapproved_species_to_the_game():
    active = json.loads((ROOT / "data/kyouryuu.json").read_text())
    assert len(active) == 10
    assert not EXPECTED.intersection(item["key"] for item in active)
