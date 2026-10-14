"""Exercise the local launcher with a fake engine, never opening user apps."""

import os
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "godot/きのこゲームを起動.command"


def _prepare_launcher(tmp_path, *, imported):
    repo = tmp_path / "isolated repo"
    project = repo / "godot"
    project.mkdir(parents=True)
    launcher = project / LAUNCHER.name
    shutil.copyfile(LAUNCHER, launcher)
    (project / "data").mkdir()
    (project / "data/kinoko.json").write_text("[]", encoding="utf-8")
    (project / "assets/sounds").mkdir(parents=True)
    (project / "assets/sounds/correct_pingpong.wav").write_bytes(b"test sound")
    if imported:
        (project / ".godot/imported").mkdir(parents=True)
        (project / ".godot/imported/test.ctex").write_bytes(b"test import")
    engine = tmp_path / "fake Godot"
    engine.write_text(
        '#!/bin/bash\nprintf "%s\\n" "$*" >> "$GODOT_LAUNCH_TEST_LOG"\n',
        encoding="utf-8",
    )
    engine.chmod(0o700)
    log = tmp_path / "engine args.txt"
    environment = dict(os.environ, GODOT_BIN=str(engine), GODOT_LAUNCH_TEST_LOG=str(log))
    return launcher, project, log, environment


def test_prepared_project_starts_game_without_reimport(tmp_path):
    launcher, project, log, environment = _prepare_launcher(tmp_path, imported=True)
    result = subprocess.run(
        ["/bin/bash", str(launcher)], env=environment, capture_output=True,
        text=True, timeout=10, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert log.read_text().splitlines() == [f"--path {project}"]
    assert "きどうします" in result.stdout


def test_first_launch_imports_assets_before_starting_game(tmp_path):
    launcher, project, log, environment = _prepare_launcher(tmp_path, imported=False)
    result = subprocess.run(
        ["/bin/bash", str(launcher)], env=environment, capture_output=True,
        text=True, timeout=10, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert log.read_text().splitlines() == [
        f"--headless --editor --path {project} --import",
        f"--path {project}",
    ]


def test_launcher_is_executable_and_shell_syntax_is_valid():
    assert os.access(LAUNCHER, os.X_OK)
    subprocess.run(["/bin/bash", "-n", str(LAUNCHER)], check=True)


def test_updated_assets_are_reimported_even_when_cache_exists(tmp_path):
    launcher, project, log, environment = _prepare_launcher(tmp_path, imported=True)
    python_bin = project.parent / ".venv/bin/python"
    python_bin.parent.mkdir(parents=True)
    python_bin.write_text(
        '#!/bin/bash\nif [[ "$*" == *"--check"* ]]; then exit 1; fi\nexit 0\n',
        encoding="utf-8",
    )
    python_bin.chmod(0o700)
    result = subprocess.run(
        ["/bin/bash", str(launcher)], env=environment, capture_output=True,
        text=True, timeout=10, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert log.read_text().splitlines() == [
        f"--headless --editor --path {project} --import",
        f"--path {project}",
    ]
