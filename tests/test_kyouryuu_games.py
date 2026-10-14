from hashlib import sha256
from pathlib import Path
import random

import pytest

from data.subject_data import load_ready_subject_items
from src.paths import KYOURYUU_DATA_PATH, KYOURYUU_FOSSIL_IMAGE_DIR, KYOURYUU_RECONSTRUCTION_IMAGE_DIR
from src.quiz import create_quiz_session


ROOT = Path(__file__).resolve().parents[1]
REVIEW_DIR = ROOT / "assets/images/kyouryuu/review/transparent"
ADDITION_KEYS = (
    "coelacanth", "ankylosaurus", "parasaurolophus", "trilobite",
    "anomalocaris", "ottoia", "mammoth", "smilodon",
)


def test_every_prehistoric_animal_has_a_fossil_and_reconstruction_image():
    items = load_ready_subject_items(KYOURYUU_DATA_PATH)

    assert len(items) == 18
    for item in items:
        assert (KYOURYUU_FOSSIL_IMAGE_DIR / item.image_filename).is_file()
        assert (KYOURYUU_RECONSTRUCTION_IMAGE_DIR / item.image_filename).is_file()


@pytest.mark.parametrize("directory, original_digest", [
    (KYOURYUU_FOSSIL_IMAGE_DIR, "185d478e5233ff480773a3a48c6e48b50f47b41262c4a5c102ad3b3de8baecd6"),
    (KYOURYUU_RECONSTRUCTION_IMAGE_DIR, "26a36fb6fd4ee959d8a88ef3996506ec68daba96b54d1957e5a29f03d438770f"),
])
def test_existing_ten_canonical_images_keep_their_original_bytes(directory, original_digest):
    items = load_ready_subject_items(KYOURYUU_DATA_PATH)

    # The ordered bytes pin the original ten assets independently of review copies.
    original_bytes = b"".join((directory / item.image_filename).read_bytes() for item in items[:10])
    assert sha256(original_bytes).hexdigest() == original_digest


@pytest.mark.parametrize("key", ADDITION_KEYS)
def test_added_canonical_image_pair_matches_the_approved_v2_sources(key):
    assert (KYOURYUU_FOSSIL_IMAGE_DIR / f"{key}.png").read_bytes() == (REVIEW_DIR / f"{key}-fossil-v2.png").read_bytes()
    assert (KYOURYUU_RECONSTRUCTION_IMAGE_DIR / f"{key}.png").read_bytes() == (REVIEW_DIR / f"{key}-reconstruction-v2.png").read_bytes()


@pytest.mark.parametrize("question_count", [5, 10])
def test_dinosaur_quiz_has_unique_questions_and_three_choices_including_every_addition(question_count):
    items = load_ready_subject_items(KYOURYUU_DATA_PATH)
    seen_answers = set()

    for seed in range(20):
        session = create_quiz_session(items, question_count, random.Random(seed))
        assert session.total_questions == question_count
        assert len({question.answer.key for question in session.questions}) == question_count
        for question in session.questions:
            seen_answers.add(question.answer.key)
            assert question.answer in question.choices
            assert len(question.choices) == 3
            assert len({choice.key for choice in question.choices}) == 3
            assert all(choice in items for choice in question.choices)

    assert seen_answers == {item.key for item in items}
    assert set(ADDITION_KEYS) <= seen_answers
