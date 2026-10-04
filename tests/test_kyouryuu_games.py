from pathlib import Path

from data.subject_data import load_ready_subject_items
from src.paths import KYOURYUU_DATA_PATH, KYOURYUU_FOSSIL_IMAGE_DIR, KYOURYUU_RECONSTRUCTION_IMAGE_DIR
from src.quiz import create_quiz_session


def test_every_prehistoric_animal_has_a_fossil_and_reconstruction_image():
    items = load_ready_subject_items(KYOURYUU_DATA_PATH)

    assert len(items) == 10
    for item in items:
        assert (KYOURYUU_FOSSIL_IMAGE_DIR / item.image_filename).is_file()
        assert (KYOURYUU_RECONSTRUCTION_IMAGE_DIR / item.image_filename).is_file()


def test_dinosaur_quiz_has_three_reconstruction_choices_for_each_fossil_question():
    items = load_ready_subject_items(KYOURYUU_DATA_PATH)
    session = create_quiz_session(items, 5)

    for question in session.questions:
        assert question.answer in question.choices
        assert len(question.choices) == 3
        assert len({choice.key for choice in question.choices}) == 3
