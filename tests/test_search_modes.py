"""恐竜さがし2モードの出題、再挑戦、画像とクリック範囲を検証する。"""

from itertools import combinations
from math import hypot
from pathlib import Path
import random

from PIL import Image, ImageChops
import pytest

from data.subject_data import SubjectItem
from src.search import _sprite, create_search_session, render_scene, status_text


ITEMS = tuple(
    SubjectItem(f"animal_{index}", f"なかま {index}", "ひんと", "せつめい")
    for index in range(10)
)
MODES = ("fossil", "reconstruction")


@pytest.mark.parametrize("mode", MODES)
def test_five_rounds_have_unique_targets_and_two_distinct_decoys(mode):
    for seed in range(50):
        history = ()
        correct_count = 0
        randomizer = random.Random(seed)
        for index in range(5):
            session = create_search_session(
                ITEMS, (Path("background.png"),), randomizer,
                current_index=index, correct_count=correct_count,
                mode=mode, used_target_keys=history, unique_targets=True,
            )
            assert session.mode == mode
            assert session.target.item.key not in history
            assert session.used_target_keys == (*history, session.target.item.key)
            assert len({placement.item.key for placement in session.placements}) == 3
            assert session.progress_text == f"もんだい {index + 1} / 5"
            assert session.is_last_question is (index == 4)
            assert session.choose_at(session.target.x, session.target.y)
            history = session.used_target_keys
            correct_count = session.correct_count
        assert len(set(history)) == 5
        assert correct_count == 5


@pytest.mark.parametrize("mode", MODES)
def test_misses_allow_unlimited_retry_and_a_correct_answer_counts_once(mode):
    session = create_search_session(ITEMS, (Path("background.png"),), random.Random(3), mode=mode)
    for _ in range(30):
        for decoy in session.decoys:
            assert not session.choose_at(decoy.x, decoy.y)
        assert not session.choose_at(0, 0)
        assert not session.is_correct
        assert session.correct_count == 0
        assert session.current_index == 0
    assert "もういちど" in status_text(session, clicked=True)
    assert session.choose_at(session.target.x, session.target.y)
    for _ in range(10):
        assert not session.choose_at(session.target.x, session.target.y)
    assert session.is_correct
    assert session.correct_count == 1
    assert session.current_index == 0


def test_unique_target_exhaustion_and_duplicate_item_keys_are_handled():
    with pytest.raises(ValueError, match="no unused search targets"):
        create_search_session(
            ITEMS, (Path("background.png"),),
            used_target_keys=tuple(item.key for item in ITEMS), unique_targets=True,
        )
    with pytest.raises(ValueError, match="three distinct items"):
        create_search_session((ITEMS[0], ITEMS[0], ITEMS[1]), (Path("background.png"),))
    session = create_search_session((*ITEMS, ITEMS[0]), (Path("background.png"),), random.Random(2))
    assert len({placement.item.key for placement in session.placements}) == 3


def test_fossil_instructions_mention_strata():
    fossil = create_search_session(ITEMS, (Path("background.png"),), mode="fossil")
    reconstruction = create_search_session(ITEMS, (Path("background.png"),), mode="reconstruction")
    assert "ちそうの なか" in status_text(fossil)
    assert "もりの なか" in status_text(reconstruction)


def test_preserved_sprite_keeps_blue_pale_translucent_and_transparent_pixels(tmp_path):
    source = Image.new("RGBA", (4, 3), (25, 160, 240, 255))
    source.putpixel((0, 0), (242, 244, 247, 255))
    source.putpixel((1, 0), (30, 170, 250, 128))
    source.putpixel((2, 0), (90, 160, 245, 0))
    path = tmp_path / "blue_animal.png"
    source.save(path)

    preserved = _sprite(path, 100, preserve_colors=True)
    assert preserved.size == source.size
    assert preserved.tobytes() == source.tobytes()
    # 既存の青い背景を抜くきのこ表示は引き続き使える。
    legacy = _sprite(path, 100)
    assert legacy.getpixel((0, 0)) == (242, 244, 247, 255)


def _color_mask(image, color):
    red, green, blue = image.split()
    masks = [
        channel.point(lambda value, expected=expected: 255 if value == expected else 0)
        for channel, expected in zip((red, green, blue), color)
    ]
    return ImageChops.multiply(ImageChops.multiply(masks[0], masks[1]), masks[2])


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("scene_size", ((600, 600), (1000, 600), (600, 1000)))
def test_whole_sprites_are_centered_inside_disjoint_click_areas(tmp_path, mode, scene_size):
    background_path = tmp_path / "background.png"
    Image.new("RGB", scene_size, (20, 30, 40)).save(background_path)
    colors = ((25, 160, 240), (242, 244, 247), (190, 70, 120))
    source_sizes = ((800, 800), (1600, 200), (200, 1600))
    paths = {}
    for item, color, size in zip(ITEMS, colors, source_sizes):
        path = tmp_path / f"custom_{item.key}.png"
        Image.new("RGBA", size, (*color, 255)).save(path)
        paths[item.key] = path
    color_by_key = dict(zip((item.key for item in ITEMS), colors))

    for seed in range(6):
        session = create_search_session(ITEMS[:3], (background_path,), random.Random(seed), mode=mode)
        scene = render_scene(session, paths)
        assert scene.size == scene_size
        for first, second in combinations(session.placements, 2):
            assert hypot(first.x - second.x, first.y - second.y) > first.radius + second.radius
        for placement in session.placements:
            color = color_by_key[placement.item.key]
            left, top, right, bottom = _color_mask(scene, color).getbbox()
            assert 0 <= left < right <= scene.width
            assert 0 <= top < bottom <= scene.height
            assert abs((left + right) / 2 - placement.x * scene.width) <= 1
            assert abs((top + bottom) / 2 - placement.y * scene.height) <= 1
            corners = ((left, top), (right - 1, top), (left, bottom - 1), (right - 1, bottom - 1))
            for x, y in corners:
                assert placement.contains(x / scene.width, y / scene.height)
            assert scene.crop((left, top, right, bottom)).getextrema() == tuple(
                (value, value) for value in color
            )


@pytest.mark.parametrize("mode", MODES)
def test_success_circle_encloses_the_whole_target(tmp_path, mode):
    background_path = tmp_path / "background.png"
    Image.new("RGB", (600, 600), (20, 30, 40)).save(background_path)
    paths = {}
    for item in ITEMS[:3]:
        path = tmp_path / item.image_filename
        Image.new("RGBA", (300, 300), (25, 160, 240, 255)).save(path)
        paths[item.key] = path
    session = create_search_session(ITEMS[:3], (background_path,), random.Random(7), mode=mode)
    before = render_scene(session, paths)
    assert session.choose_at(session.target.x, session.target.y)
    after = render_scene(session, paths)
    yellow = _color_mask(after, (255, 212, 59))
    left, top, right, bottom = yellow.getbbox()
    center_x, center_y = session.target.x * after.width, session.target.y * after.height
    assert 0 <= left < right <= after.width
    assert 0 <= top < bottom <= after.height
    sprite_half_side = int(min(after.size) * 0.19) / 2
    corner_distance = hypot(sprite_half_side, sprite_half_side)
    ring_pixels = yellow.crop((left, top, right, bottom))
    for y in range(ring_pixels.height):
        for x in range(ring_pixels.width):
            if ring_pixels.getpixel((x, y)):
                assert hypot(left + x - center_x, top + y - center_y) > corner_distance
    target_frame = (
        int(center_x - sprite_half_side), int(center_y - sprite_half_side),
        int(center_x + sprite_half_side), int(center_y + sprite_half_side),
    )
    assert before.crop(target_frame).tobytes() == after.crop(target_frame).tobytes()


def test_directory_image_source_remains_supported(tmp_path):
    background_path = tmp_path / "background.png"
    Image.new("RGB", (600, 400), (20, 30, 40)).save(background_path)
    for item in ITEMS[:3]:
        Image.new("RGBA", (100, 100), (190, 70, 120, 255)).save(tmp_path / item.image_filename)
    session = create_search_session(ITEMS[:3], (background_path,), random.Random(4))
    assert session.mode == "default"
    assert render_scene(session, tmp_path).size == (600, 400)
