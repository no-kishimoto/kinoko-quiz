"""Catalogue additions require the separate description, image and hint approvals."""

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
    assert "Gradio search, quiz and encyclopedia use all 18 species" in review["game_integration"]
    assert review["quiz_hint_approval"] == {
        "date": "2026-10-14",
        "keys": [item["key"] for item in candidates],
    }
    assert review["catalogue_integration"]["date"] == "2026-10-14"
    assert review["catalogue_integration"]["active_species_count"] == 18
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


def test_approved_additions_are_active_with_confirmed_quiz_hints():
    active = json.loads((ROOT / "data/kyouryuu.json").read_text())
    candidates = json.loads((ROOT / "data/kyouryuu_candidates.json").read_text())
    active_by_key = {item["key"]: item for item in active}
    assert len(active) == len(active_by_key) == 18
    assert EXPECTED <= set(active_by_key)
    for candidate in candidates:
        item = active_by_key[candidate["key"]]
        assert candidate["quiz_hint_status"] == "approved"
        assert candidate["quiz_hint_approval_date"] == "2026-10-14"
        assert item["quiz_hint"] == candidate["quiz_hint"]
        assert item["zukan_text"] == candidate["zukan_text"]
