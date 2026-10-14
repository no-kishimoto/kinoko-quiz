"""Godot uses exact approved mushroom originals, never regenerated cutouts."""

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from scripts.sync_godot_kinoko import AssetSyncError, MANIFEST_PATH, ROOT, sync_assets


@pytest.fixture(scope="module")
def prepared_project(tmp_path_factory):
    root = tmp_path_factory.mktemp("godot-mushroom-project")
    (root / "data").mkdir()
    shutil.copyfile(ROOT / "data/kinoko.json", root / "data/kinoko.json")
    entries = json.loads((root / "data/kinoko.json").read_text(encoding="utf-8"))
    for directory in ("assets/images/quiz", "assets/images/zukan"):
        (root / directory).mkdir(parents=True)
        for item in entries:
            filename = f"{item['key']}.png"
            shutil.copyfile(ROOT / directory / filename, root / directory / filename)
    (root / "assets/sounds").mkdir(parents=True)
    shutil.copyfile(ROOT / "assets/sounds/correct_pingpong.wav", root / "assets/sounds/correct_pingpong.wav")
    manifest = sync_assets(root)
    return root, manifest


def test_synced_catalogue_and_images_are_exact_original_bytes(prepared_project):
    root, manifest = prepared_project
    data_bytes = (root / "godot/data/kinoko.json").read_bytes()
    assert data_bytes == (ROOT / "data/kinoko.json").read_bytes()
    entries = json.loads(data_bytes)
    assert len(entries) == len({item["key"] for item in entries}) == 30
    assert manifest["species_count"] == 30
    assert len(manifest["files"]) == 62
    for relative, entry in manifest["files"].items():
        data = (root / "godot" / relative).read_bytes()
        assert data == (ROOT / relative).read_bytes(), relative
        assert hashlib.sha256(data).hexdigest() == entry["sha256"], relative
        assert len(data) == entry["bytes"], relative
    assert json.loads((root / "godot" / MANIFEST_PATH).read_bytes()) == manifest


def test_only_correct_sound_is_prepared(prepared_project):
    root, manifest = prepared_project
    sounds = [path for path in manifest["files"] if path.startswith("assets/sounds/")]
    assert sounds == ["assets/sounds/correct_pingpong.wav"]
    assert sorted(path.name for path in (root / "godot/assets/sounds").iterdir()) == ["correct_pingpong.wav"]


def test_repeated_sync_reuses_manifest_and_preserves_unrelated_files(prepared_project):
    root, manifest = prepared_project
    unrelated = root / "godot/assets/unrelated-user-file.txt"
    unrelated.write_text("leave this file alone", encoding="utf-8")
    manifest_path = root / "godot" / MANIFEST_PATH
    before = {path: (root / "godot" / path).stat().st_mtime_ns for path in manifest["files"]}
    manifest_time = manifest_path.stat().st_mtime_ns
    assert sync_assets(root) == manifest
    assert sync_assets(root, check_only=True) == manifest
    assert manifest_path.stat().st_mtime_ns == manifest_time
    assert unrelated.read_text(encoding="utf-8") == "leave this file alone"
    assert before == {path: (root / "godot" / path).stat().st_mtime_ns for path in manifest["files"]}


def test_missing_asset_fails_before_destination_is_created(tmp_path):
    (tmp_path / "data").mkdir()
    shutil.copyfile(ROOT / "data/kinoko.json", tmp_path / "data/kinoko.json")
    with pytest.raises(AssetSyncError, match="Missing source assets"):
        sync_assets(tmp_path)
    assert not (tmp_path / "godot").exists()


def test_invalid_keys_cannot_escape_known_destinations(tmp_path):
    (tmp_path / "data").mkdir()
    entries = json.loads((ROOT / "data/kinoko.json").read_text(encoding="utf-8"))
    entries[0]["key"] = "../../outside"
    (tmp_path / "data/kinoko.json").write_text(json.dumps(entries), encoding="utf-8")
    with pytest.raises(AssetSyncError, match="keys must be valid"):
        sync_assets(tmp_path)
    assert not (tmp_path / "godot").exists()


def test_check_mode_detects_changed_resource_without_modifying_it(prepared_project):
    root, _ = prepared_project
    path = root / "godot/assets/sounds/correct_pingpong.wav"
    original = path.read_bytes()
    try:
        path.write_bytes(b"changed")
        with pytest.raises(AssetSyncError, match="need synchronization"):
            sync_assets(root, check_only=True)
        assert path.read_bytes() == b"changed"
    finally:
        path.write_bytes(original)
