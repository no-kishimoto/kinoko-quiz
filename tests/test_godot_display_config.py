"""Guard the PC/Retina display settings that must not shrink into editor preview."""

from configparser import ConfigParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_game_starts_maximized_with_responsive_canvas():
    settings = ConfigParser(interpolation=None)
    # Godot has an unsectioned config_version header before its INI sections.
    settings.read_string(
        "[godot_header]\n" + (ROOT / "godot/project.godot").read_text(encoding="utf-8")
    )
    display = settings["display"]
    assert display.getint("window/size/mode") == 2  # Window.MODE_MAXIMIZED
    assert display.getint("window/size/viewport_width") == 1280
    assert display.getint("window/size/viewport_height") == 800
    assert display.getint("window/size/window_width_override") >= 1280
    assert display.getint("window/size/window_height_override") >= 800
    assert display["window/stretch/mode"] == '"canvas_items"'
    assert display["window/stretch/aspect"] == '"expand"'
