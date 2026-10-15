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
    (project / "data/game_catalog.json").write_text("{}", encoding="utf-8")
    (project / "assets/sounds").mkdir(parents=True)
    (project / "assets/sounds/correct_pingpong.wav").write_bytes(b"test sound")
    (project / "assets/game_manifest.json").write_text("{}", encoding="utf-8")
    if imported:
        (project / ".godot/imported").mkdir(parents=True)
        (project / ".godot/imported/test.ctex").write_bytes(b"test import")
        (project / ".godot/full-assets-imported").touch()
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
    assert (project / ".godot/full-assets-imported").is_file()


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


def test_launcher_prepares_all_subjects_and_never_downloads_or_removes_files():
    source = LAUNCHER.read_text(encoding="utf-8")
    assert "scripts/sync_godot_assets.py" in source
    assert "scripts/sync_godot_kinoko.py" not in source
    assert "data/game_catalog.json" in source
    assert "assets/game_manifest.json" in source
    for command in ("curl ", "wget ", "pip install", "git clone", "rm -", "shutil.rmtree"):
        assert command not in source


def test_partial_import_cache_without_readiness_marker_is_imported_again(tmp_path):
    launcher, project, log, environment = _prepare_launcher(tmp_path, imported=True)
    marker = project / ".godot/full-assets-imported"
    marker.unlink()
    result = subprocess.run(
        ["/bin/bash", str(launcher)], env=environment, capture_output=True,
        text=True, timeout=10, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert log.read_text().splitlines() == [
        f"--headless --editor --path {project} --import",
        f"--path {project}",
    ]
    assert marker.is_file()


def test_failed_import_does_not_mark_ready_and_next_launch_retries(tmp_path):
    launcher, project, log, environment = _prepare_launcher(tmp_path, imported=True)
    marker = project / ".godot/full-assets-imported"
    marker.unlink()
    engine = Path(environment["GODOT_BIN"])
    successful_engine = engine.read_text(encoding="utf-8")
    engine.write_text(successful_engine + 'if [[ "$*" == *"--import"* ]]; then exit 42; fi\n', encoding="utf-8")
    failed = subprocess.run(
        ["/bin/bash", str(launcher)], env=environment, capture_output=True,
        text=True, timeout=10, check=False,
    )
    assert failed.returncode == 42
    assert not marker.exists()
    assert log.read_text().splitlines() == [f"--headless --editor --path {project} --import"]
    engine.write_text(successful_engine, encoding="utf-8")
    retry = subprocess.run(
        ["/bin/bash", str(launcher)], env=environment, capture_output=True,
        text=True, timeout=10, check=False,
    )
    assert retry.returncode == 0, retry.stderr
    assert marker.is_file()
    assert log.read_text().splitlines() == [
        f"--headless --editor --path {project} --import",
        f"--headless --editor --path {project} --import",
        f"--path {project}",
    ]


def test_manifest_updated_after_ready_marker_forces_import(tmp_path):
    launcher, project, log, environment = _prepare_launcher(tmp_path, imported=True)
    marker = project / ".godot/full-assets-imported"
    manifest = project / "assets/game_manifest.json"
    old_time = manifest.stat().st_mtime_ns - 2_000_000_000
    os.utime(marker, ns=(old_time, old_time))
    result = subprocess.run(
        ["/bin/bash", str(launcher)], env=environment, capture_output=True,
        text=True, timeout=10, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert log.read_text().splitlines() == [
        f"--headless --editor --path {project} --import",
        f"--path {project}",
    ]
    assert marker.stat().st_mtime_ns >= manifest.stat().st_mtime_ns


def test_failed_repair_invalidates_previous_success_even_if_manifest_is_unchanged(tmp_path):
    launcher, project, log, environment = _prepare_launcher(tmp_path, imported=True)
    marker = project / ".godot/full-assets-imported"
    manifest = project / "assets/game_manifest.json"
    python_bin = project.parent / ".venv/bin/python"
    python_bin.parent.mkdir(parents=True)
    python_bin.write_text(
        '#!/bin/bash\nif [[ "$*" == *"--check"* ]]; then exit 1; fi\nexit 0\n',
        encoding="utf-8",
    )
    python_bin.chmod(0o700)
    engine = Path(environment["GODOT_BIN"])
    successful_engine = engine.read_text(encoding="utf-8")
    engine.write_text(successful_engine + 'if [[ "$*" == *"--import"* ]]; then exit 42; fi\n', encoding="utf-8")
    failed = subprocess.run(
        ["/bin/bash", str(launcher)], env=environment, capture_output=True,
        text=True, timeout=10, check=False,
    )
    assert failed.returncode == 42
    assert marker.stat().st_mtime_ns < manifest.stat().st_mtime_ns
    # Sources are now prepared, but the interrupted import must still retry.
    python_bin.write_text('#!/bin/bash\nexit 0\n', encoding="utf-8")
    engine.write_text(successful_engine, encoding="utf-8")
    retry = subprocess.run(
        ["/bin/bash", str(launcher)], env=environment, capture_output=True,
        text=True, timeout=10, check=False,
    )
    assert retry.returncode == 0, retry.stderr
    assert log.read_text().splitlines() == [
        f"--headless --editor --path {project} --import",
        f"--headless --editor --path {project} --import",
        f"--path {project}",
    ]
    assert marker.stat().st_mtime_ns >= manifest.stat().st_mtime_ns
