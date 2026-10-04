"""Gradioのさがし画面で、モードと5問の進行を確かめる。"""

from pathlib import Path
import re
from types import SimpleNamespace

import gradio as gr
from PIL import Image
import pytest

from src import ui
from src.dinosaur_search import load_dinosaur_search_assets
from src.search import SearchSession


def _component(app, component_type, value=None, elem_class=None):
    matches = [
        component for component in app.blocks.values()
        if isinstance(component, component_type)
        and (value is None or getattr(component, "value", None) == value)
        and (elem_class is None or elem_class in component.elem_classes)
    ]
    assert len(matches) == 1
    return matches[0]


def _callback(app, name):
    matches = [callback for callback in app.fns.values() if callback.fn.__name__ == name]
    assert len(matches) == 1
    return matches[0]


def _button_callback(app, label):
    button = _component(app, gr.Button, value=label)
    return _click_callback(app, button)


def _click_callback(app, button):
    matches = [
        callback for callback in app.fns.values()
        if (button._id, "click") in callback.targets
    ]
    assert len(matches) == 1
    return matches[0]


def _invoke(callback, *args):
    updates = callback.fn(*args)
    # Every returned change must be wired to an actual Gradio output.
    assert set(updates).issubset(callback.outputs)
    return updates


def _session(updates):
    sessions = [value for value in updates.values() if isinstance(value, SearchSession)]
    assert len(sessions) == 1
    return sessions[0]


def _click(game, session, placement=None, index=None):
    if index is None:
        with Image.open(session.background_path) as background:
            width, height = background.size
        index = (placement.x * width, placement.y * height)
    event = gr.SelectData(game.scene, {"index": index, "value": None})
    return _invoke(game.click, session, "kyouryuu", event)


@pytest.fixture
def game_factory(monkeypatch):
    assets = load_dinosaur_search_assets()
    apps = []

    def make_game(reconstruction_ready=False):
        if reconstruction_ready:
            # Model the approved complete catalog without using pending files.
            current_assets = SimpleNamespace(
                items=assets.items,
                specimen_images=assets.specimen_images,
                reconstruction_images={
                    item.key: Path("/approved/living") / item.image_filename
                    for item in assets.items
                },
                backgrounds=assets.backgrounds,
                reconstruction_ready=True,
                pending_reconstruction_keys=(),
            )
        else:
            current_assets = assets
        monkeypatch.setattr(ui, "load_dinosaur_search_assets", lambda: current_assets)
        render_calls = []

        def record_render(session, image_sources):
            render_calls.append((session, image_sources))
            return Image.new("RGB", (120, 80), "white")

        monkeypatch.setattr(ui, "render_scene", record_render)
        app = ui.build_app()
        apps.append(app)
        return SimpleNamespace(
            app=app,
            assets=current_assets,
            render_calls=render_calls,
            start_fossil=_button_callback(app, "かせきさがし"),
            start_living=_callback(app, "start_search"),
            click=_callback(app, "search_click"),
            next=_callback(app, "next_search"),
            scene=_component(app, gr.Image, elem_class="search-scene"),
            next_button=_component(app, gr.Button, value="つぎの もんだい"),
            sound=_component(app, gr.HTML, elem_class="sound-effect"),
            result=_component(app, gr.Markdown, elem_class="result-text"),
        )

    yield make_game
    for app in apps:
        app.close()


def test_dinosaur_menu_has_two_modes_and_gates_unapproved_living_images(game_factory):
    game = game_factory()
    assert len(game.assets.items) == 18
    assert game.assets.reconstruction_ready is False
    assert len(game.assets.reconstruction_images) == 8
    assert len(game.assets.pending_reconstruction_keys) == 10
    assert not set(game.assets.pending_reconstruction_keys) & set(game.assets.reconstruction_images)

    menu = _button_callback(game.app, "🦖 きょうりゅう")
    updates = _invoke(menu)
    living_button = _component(game.app, gr.Button, value="きのこ さがし")
    fossil_button = _component(game.app, gr.Button, value="かせきさがし")
    note = _component(
        game.app, gr.Markdown,
        value="きょうりゅうさがしは、のこりの えを かくにんしてから あそべるよ。",
    )
    assert updates[living_button].value == "きょうりゅうさがし"
    assert updates[living_button].interactive is False
    assert updates[fossil_button].visible is True
    assert updates[fossil_button].interactive is True
    assert updates[note].visible is True
    assert not re.search(r"[\u3400-\u4dbf\u4e00-\u9fff]", note.value)

    with pytest.raises(gr.Error, match="のこりの えを かくにん"):
        _invoke(game.start_living, "kyouryuu")
    assert game.render_calls == []


def test_search_scene_displays_only_and_keeps_the_select_event(game_factory):
    game = game_factory()
    scene_config = next(
        component["props"] for component in game.app.config["components"]
        if component["id"] == game.scene._id
    )
    assert scene_config["interactive"] is False
    assert scene_config["sources"] == []
    assert scene_config["buttons"] == []
    assert scene_config["_selectable"] is True
    assert (game.scene._id, "select") in game.click.targets
    select_dependency = next(
        dependency for dependency in game.app.config["dependencies"]
        if (game.scene._id, "select") in dependency["targets"]
    )
    assert select_dependency["collects_event_data"] is True

    started = _invoke(game.start_fossil, "kyouryuu")
    session = _session(started)
    clicked = _click(game, session, placement=session.target)
    assert _session(clicked).is_correct is True
    assert clicked[game.next_button].visible is True


def test_shared_sound_is_mounted_outside_every_hidden_screen(game_factory):
    game = game_factory()
    root_children = game.app.config["layout"]["children"]
    assert any(child["id"] == game.sound._id for child in root_children)
    sound_config = next(
        component["props"] for component in game.app.config["components"]
        if component["id"] == game.sound._id
    )
    assert sound_config["visible"] is True
    assert game.sound in game.click.outputs
    assert game.sound in game.start_fossil.outputs
    assert game.sound in game.next.outputs


@pytest.mark.parametrize(
    ("game_name", "start_label", "next_name"),
    [
        ("quiz", "5もん", "go_next"),
        ("addition", "たしざんで あそぶ", "next_math"),
        ("subtraction", "ひきざんで あそぶ", "next_math"),
    ],
)
def test_quiz_and_math_keep_shared_correct_audio_and_clear_it_on_next_and_result(
    game_factory, game_name, start_label, next_name,
):
    game = game_factory()
    starter = _button_callback(game.app, start_label)
    started = _invoke(starter, "kinoko")
    session_state = starter.outputs[0]
    session = started[session_state]
    assert started[game.sound] in (None, "")
    choice_buttons = [
        component for component in started
        if isinstance(component, gr.Button) and "choice" in component.elem_classes
    ]
    assert len(choice_buttons) == 3
    next_callback = _callback(game.app, next_name)
    for _ in session.questions:
        question = session.current_question if game_name == "quiz" else session.question
        answer_index = question.choices.index(question.answer)
        answer_callback = _click_callback(game.app, choice_buttons[answer_index])
        answered = (
            _invoke(answer_callback, session, "kinoko") if game_name == "quiz"
            else _invoke(answer_callback, session)
        )
        assert "<audio autoplay" in answered[game.sound]
        assert "data:audio/wav;base64," in answered[game.sound]
        session = answered[session_state]
        advanced = _invoke(next_callback, session, "kinoko")
        assert advanced[game.sound] in (None, "")
        session = advanced[session_state]
    assert session.is_finished is True


@pytest.mark.parametrize(
    ("subject", "button_label", "search_label"),
    [
        ("kinoko", "🍄 きのこ", "きのこ さがし"),
        ("shokubutsu", "🌱 しょくぶつ", "しょくぶつ さがし"),
        ("konchuu", "🪲 こんちゅう", "こんちゅう さがし"),
    ],
)
def test_other_subject_menus_and_search_sources_still_work(
    game_factory, subject, button_label, search_label,
):
    game = game_factory()
    updates = _invoke(_button_callback(game.app, button_label))
    living_button = _component(game.app, gr.Button, value="きのこ さがし")
    fossil_button = _component(game.app, gr.Button, value="かせきさがし")
    assert updates[living_button].value == search_label
    assert updates[living_button].interactive is True
    assert updates[fossil_button].visible is False

    started = _invoke(game.start_living, subject)
    session = _session(started)
    assert session.mode == "default"
    assert session.background_path.parent == ui.SEARCH_BACKGROUND_DIR
    assert isinstance(game.render_calls[-1][1], Path)
    assert started[game.sound] == ""


@pytest.mark.parametrize("mode", ["fossil", "reconstruction"])
def test_dinosaur_search_keeps_mode_and_unique_targets_for_five_questions(game_factory, mode):
    game = game_factory(reconstruction_ready=mode == "reconstruction")
    starter = game.start_fossil if mode == "fossil" else game.start_living
    updates = _invoke(starter, "kyouryuu")
    session = _session(updates)
    heading = game.start_fossil.outputs[4]
    prompt = game.start_fossil.outputs[6]
    status = game.start_fossil.outputs[7]
    expected_label = "かせきさがし" if mode == "fossil" else "きょうりゅうさがし"
    image_sources = (
        game.assets.specimen_images if mode == "fossil"
        else game.assets.reconstruction_images
    )
    assert updates[heading] == f"# {expected_label}"
    assert session.target.item.name in updates[prompt]
    assert ("ちそう" if mode == "fossil" else "もり") in updates[status]
    assert updates[game.next_button].visible is False
    assert len(session.decoys) == 2
    assert len({placement.item.key for placement in session.placements}) == 3

    found_keys = []
    for question_index in range(5):
        assert session.mode == mode
        assert session.current_index == question_index
        assert session.total_questions == 5
        assert session.target.item.key not in found_keys
        assert tuple(session.used_target_keys) == (*found_keys, session.target.item.key)
        assert game.render_calls[-1][1] is image_sources
        if mode == "fossil":
            assert session.background_path in game.assets.backgrounds
        else:
            assert session.background_path.parent == ui.SEARCH_BACKGROUND_DIR

        with pytest.raises(gr.Error, match="みつけてから"):
            _invoke(game.next, session, "kyouryuu")
        wrong = _click(game, session, placement=session.decoys[0])
        session = _session(wrong)
        assert session.is_correct is False
        assert wrong[game.next_button].visible is False
        assert wrong[game.sound] == gr.skip()

        correct = _click(game, session, placement=session.target)
        session = _session(correct)
        assert session.correct_count == question_index + 1
        assert correct[game.next_button].visible is True
        assert "<audio autoplay" in correct[game.sound]
        assert "data:audio/wav;base64," in correct[game.sound]
        found_keys.append(session.target.item.key)

        # Further clicks keep Next and the playing audio without restarting it.
        for placement in (session.target, session.decoys[0]):
            repeated = _click(game, session, placement=placement)
            session = _session(repeated)
            assert repeated[game.next_button].visible is True
            assert repeated[game.sound] == gr.skip()
            assert session.correct_count == question_index + 1
        malformed = _click(game, session, index=0)
        assert malformed[game.next_button].visible is True
        assert malformed[game.sound] == gr.skip()

        updates = _invoke(game.next, session, "kyouryuu")
        assert updates[game.sound] == ""
        if question_index < 4:
            session = _session(updates)
            assert updates[game.next_button].visible is False
    assert len(set(found_keys)) == 5
    assert updates[game.result] == (
        f"# {expected_label}の けっか\n\n"
        "ぜんぶで 5もん\n\nみつけたのは 5もん"
    )


def test_ready_living_catalog_opens_button_and_hides_pending_note(game_factory):
    game = game_factory(reconstruction_ready=True)
    updates = _invoke(_button_callback(game.app, "🦖 きょうりゅう"))
    living_button = _component(game.app, gr.Button, value="きのこ さがし")
    note = _component(
        game.app, gr.Markdown,
        value="きょうりゅうさがしは、のこりの えを かくにんしてから あそべるよ。",
    )
    assert updates[living_button].interactive is True
    assert updates[note].visible is False


def test_search_title_and_result_title_clear_sound_and_reset_search(game_factory):
    game = game_factory()
    started = _invoke(game.start_fossil, "kyouryuu")
    search_state = game.start_fossil.outputs[0]
    assert _session(started).mode == "fossil"
    returned = _invoke(_callback(game.app, "search_to_title"))
    assert returned[search_state] is None
    assert returned[game.sound] == ""
    returned = _invoke(_callback(game.app, "return_to_title"))
    assert returned[search_state] is None
    assert returned[game.sound] == ""

    # The result screen has a single action: return to the title.
    result_screen = game.next.outputs[2]

    def layout_node(node):
        if node.get("id") == result_screen._id:
            return node
        for child in node.get("children", []):
            found = layout_node(child)
            if found is not None:
                return found
        return None

    result_layout = layout_node(game.app.config["layout"])
    button_labels = [
        game.app.blocks[child["id"]].value for child in result_layout["children"]
        if isinstance(game.app.blocks[child["id"]], gr.Button)
    ]
    assert button_labels == ["タイトルへ もどる"]
