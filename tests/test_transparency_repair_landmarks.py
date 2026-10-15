"""Human-reviewed negative spaces and a restored wing must stay correct.

These normalized landmarks are specific to the approved illustrations, not
an automatic color-based segmentation rule. White body parts remain visible.
"""

from pathlib import Path

import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parents[1] / "assets/images"

GAPS = (
    ("konchuu", "ari", (0.60, 0.29)),
    ("konchuu", "koorogi", (0.70, 0.34)),
    ("konchuu", "kamakiri", (0.15, 0.44)),
    ("konchuu", "batta", (0.65, 0.40)),
    ("konchuu", "batta", (0.80, 0.45)),
    ("konchuu", "ka", (0.485, 0.22)),
    ("konchuu", "girafanokogirikuwagata", (0.66, 0.435)),
    ("shokubutsu", "utsubokazura", (0.75, 0.49)),
    ("shokubutsu", "utsubokazura", (0.73, 0.55)),
    ("shokubutsu", "piiman", (0.53, 0.40)),
    ("shokubutsu", "momiji", (0.36, 0.56)),
    ("shokubutsu", "momiji", (0.40, 0.58)),
)


@pytest.mark.parametrize("directory", ("zukan", "quiz"))
@pytest.mark.parametrize("subject,key,point", GAPS)
def test_reviewed_leaf_and_leg_gaps_do_not_contain_opaque_background(directory, subject, key, point):
    with Image.open(ROOT / subject / directory / f"{key}.png") as opened:
        image = opened.convert("RGBA")
    pixel = image.getpixel((int(point[0] * image.width), int(point[1] * image.height)))
    # Allow barely visible antialiasing, but never an opaque pale background.
    assert pixel[3] <= 8, (subject, key, directory, point, pixel)


@pytest.mark.parametrize("directory", ("zukan", "quiz"))
@pytest.mark.parametrize("point", ((0.73, 0.19), (0.75, 0.18)))
def test_hornet_pale_wing_is_restored_not_erased_as_background(directory, point):
    with Image.open(ROOT / "konchuu" / directory / "suzumebachi.png") as opened:
        image = opened.convert("RGBA")
    pixel = image.getpixel((int(point[0] * image.width), int(point[1] * image.height)))
    assert pixel[3] >= 245, (directory, point, pixel)


@pytest.mark.parametrize("directory", ("zukan", "quiz"))
def test_dandelion_white_seed_head_is_preserved(directory):
    with Image.open(ROOT / "shokubutsu" / directory / "tanpopo.png") as opened:
        image = opened.convert("RGBA")
    pixel = image.getpixel((int(0.62 * image.width), int(0.12 * image.height)))
    assert pixel[3] >= 245, (directory, pixel)
