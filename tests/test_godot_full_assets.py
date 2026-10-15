"""Four-subject Godot preparation retains approved RGB and alpha byte-for-byte."""

import hashlib
import json
import shutil
from pathlib import Path

import pytest
from PIL import Image

from scripts.sync_godot_assets import (
    AssetSyncError,
    CATALOG_PATH,
    MANIFEST_PATH,
    ROOT,
    SUBJECTS,
    _plan,
    _read_entries,
    sync_assets,
)
from scripts.sync_godot_kinoko import sync_assets as sync_mushroom_assets
from src.dinosaur_search import load_dinosaur_search_assets


@pytest.fixture(scope="module")
def prepared_full_project(tmp_path_factory):
    root = tmp_path_factory.mktemp("godot-four-subjects")
    _, paths = _plan(ROOT)
    review_files = [
        "assets/images/kyouryuu/review/transparent/review-overrides.json",
        "assets/images/kyouryuu/review/transparent/additions-review.json",
        "assets/images/kyouryuu/review/transparent/reconstructions/review.json",
        "assets/images/kyouryuu/review/search-backgrounds/generation.json",
        "assets/images/kyouryuu/search-backgrounds/habitats.json",
    ]
    for relative in set(paths).union(Path(name) for name in review_files):
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, destination)
    manifest = sync_assets(root)
    return root, manifest


def test_full_catalogue_has_all_four_subjects_and_117_complete_species(prepared_full_project):
    root, manifest = prepared_full_project
    catalog = json.loads((root / "godot" / CATALOG_PATH).read_text(encoding="utf-8"))
    assert catalog["format_version"] == manifest["format_version"] == 1
    assert catalog["species_count"] == manifest["species_count"] == 117
    assert set(catalog["subjects"]) == set(SUBJECTS)
    for subject, (label, count) in SUBJECTS.items():
        group = catalog["subjects"][subject]
        assert group["label"] == label
        assert len(group["items"]) == count
        assert len({item["key"] for item in group["items"]}) == count
        original = json.loads((root / f"data/{subject}.json").read_text(encoding="utf-8"))
        # Original full records, including every rich mushroom field, are kept.
        for item, source in zip(group["items"], original, strict=True):
            assert item["key"] == source["key"]
            for field, value in source.items():
                if subject != "kyouryuu" or field not in {"quiz_hint", "zukan_text"}:
                    assert item[field] == value
            for image_field in ("quiz_image", "color_image", "search_image"):
                assert item[image_field].startswith("res://assets/images/")
                assert (root / "godot" / item[image_field].removeprefix("res://")).is_file()
        assert (root / "godot" / f"data/{subject}.json").read_bytes() == (ROOT / f"data/{subject}.json").read_bytes()


def test_full_manifest_matches_every_unmodified_original(prepared_full_project):
    root, manifest = prepared_full_project
    assert json.loads((root / "godot" / MANIFEST_PATH).read_text(encoding="utf-8")) == manifest
    for relative, checksum in manifest["files"].items():
        destination = (root / "godot" / relative).read_bytes()
        assert hashlib.sha256(destination).hexdigest() == checksum["sha256"]
        assert len(destination) == checksum["bytes"]
        if relative != CATALOG_PATH.as_posix():
            assert destination == (root / relative).read_bytes(), relative
            assert destination == (ROOT / relative).read_bytes(), relative
    assert sync_mushroom_assets(root, check_only=True)["species_count"] == 30
    assert [name for name in manifest["files"] if name.startswith("assets/sounds/")] == [
        "assets/sounds/correct_pingpong.wav"
    ]


def test_dinosaurs_use_latest_independently_approved_transparency_and_descriptions(prepared_full_project):
    root, _ = prepared_full_project
    catalog = json.loads((root / "godot" / CATALOG_PATH).read_text(encoding="utf-8"))
    group = catalog["subjects"]["kyouryuu"]
    assets = load_dinosaur_search_assets(root)
    for item in group["items"]:
        key = item["key"]
        approved_fossil = "res://" + assets.specimen_images[key].relative_to(root).as_posix()
        approved_color = "res://" + assets.reconstruction_images[key].relative_to(root).as_posix()
        assert item["quiz_image"] == item["fossil_image"] == approved_fossil
        assert item["color_image"] == item["search_image"] == approved_color
    entries = {item["key"]: item for item in group["items"]}
    assert entries["tyrannosaurus"]["quiz_image"].endswith("tyrannosaurus-fossil-v3.png")
    assert "にほんの つめ" in entries["tyrannosaurus"]["zukan_text"]
    assert "よくりゅうの なかま" in entries["pteranodon"]["zukan_text"]
    assert "かいりゅうの なかま" in entries["plesiosaurus"]["zukan_text"]
    assert "かいりゅうの なかま" in entries["mosasaurus"]["zukan_text"]
    assert len(group["fossil_backgrounds"]) == 2
    assert len(group["habitat_backgrounds"]["land"]) == 2
    assert len(group["habitat_backgrounds"]["sea"]) == 1
    assert group["habitats"] == assets.habitats
    assert set(group["habitats"]) == set(entries)
    for subject in ("kinoko", "shokubutsu", "konchuu"):
        assert len(catalog["subjects"][subject]["backgrounds"]) == 4


@pytest.mark.parametrize("relative", [
    "assets/images/zukan/sorairotake.png",
    "assets/images/konchuu/zukan/monshirochou.png",
    "assets/images/konchuu/zukan/ari.png",
    "assets/images/shokubutsu/zukan/utsubokazura.png",
    "assets/images/shokubutsu/zukan/tanpopo.png",
])
def test_pale_subjects_and_small_alpha_details_are_preserved(prepared_full_project, relative):
    root, _ = prepared_full_project
    with Image.open(root / relative) as source, Image.open(root / "godot" / relative) as copied:
        assert "A" in source.getbands()
        assert copied.getchannel("A").tobytes() == source.getchannel("A").tobytes()
        assert copied.convert("RGB").tobytes() == source.convert("RGB").tobytes()


def test_repeated_full_sync_is_idempotent_and_preserves_unrelated_user_files(prepared_full_project):
    root, manifest = prepared_full_project
    extra = root / "godot/assets/keep-user-file.txt"
    extra.write_text("keep this", encoding="utf-8")
    paths = [root / "godot" / name for name in manifest["files"]]
    paths.append(root / "godot" / MANIFEST_PATH)
    before = {path: path.stat().st_mtime_ns for path in paths}
    assert sync_assets(root) == sync_assets(root, check_only=True) == manifest
    assert before == {path: path.stat().st_mtime_ns for path in paths}
    assert extra.read_text(encoding="utf-8") == "keep this"


def test_full_check_detects_corruption_without_writing(prepared_full_project):
    root, _ = prepared_full_project
    destination = root / "godot" / CATALOG_PATH
    original = destination.read_bytes()
    try:
        destination.write_bytes(b"changed")
        with pytest.raises(AssetSyncError, match="need synchronization"):
            sync_assets(root, check_only=True)
        assert destination.read_bytes() == b"changed"
    finally:
        destination.write_bytes(original)


def test_unapproved_images_fail_before_any_write(prepared_full_project):
    root, manifest = prepared_full_project
    record = root / "assets/images/kyouryuu/review/transparent/reconstructions/review.json"
    original = record.read_bytes()
    destination = root / "godot" / MANIFEST_PATH
    before = destination.stat().st_mtime_ns
    pending = json.loads(original)
    pending["items"][0]["image_status"] = "awaiting_user_review"
    try:
        record.write_text(json.dumps(pending), encoding="utf-8")
        with pytest.raises(AssetSyncError, match="independent approval"):
            sync_assets(root)
        assert destination.stat().st_mtime_ns == before
        assert json.loads(destination.read_text(encoding="utf-8")) == manifest
    finally:
        record.write_bytes(original)


def test_unsafe_destination_is_rejected_before_legacy_or_full_writes(prepared_full_project, tmp_path):
    root, _ = prepared_full_project
    destination = root / "godot" / CATALOG_PATH
    original = destination.read_bytes()
    outside = tmp_path / "outside.txt"
    outside.write_text("do not overwrite", encoding="utf-8")
    legacy_manifest = root / "godot/assets/kinoko_manifest.json"
    before = legacy_manifest.stat().st_mtime_ns
    try:
        destination.unlink()
        destination.symlink_to(outside)
        with pytest.raises(AssetSyncError, match="escapes|symbolic link"):
            sync_assets(root)
        assert outside.read_text(encoding="utf-8") == "do not overwrite"
        assert legacy_manifest.stat().st_mtime_ns == before
    finally:
        destination.unlink()
        destination.write_bytes(original)


def test_unsafe_source_is_rejected_without_creating_godot_root(tmp_path):
    folder = tmp_path / "assets/images/search/backgrounds"
    folder.mkdir(parents=True)
    (folder / "outside.png").symlink_to(ROOT / "assets/images/search/backgrounds/roots.png")
    with pytest.raises(AssetSyncError, match="escapes the repository"):
        sync_assets(tmp_path)
    assert not (tmp_path / "godot").exists()


def test_invalid_subject_keys_cannot_escape_resource_directories(tmp_path):
    (tmp_path / "data").mkdir()
    entries = json.loads((ROOT / "data/shokubutsu.json").read_text(encoding="utf-8"))
    entries[0]["key"] = "../../outside"
    (tmp_path / "data/shokubutsu.json").write_text(json.dumps(entries), encoding="utf-8")
    with pytest.raises(AssetSyncError, match="keys must be valid"):
        _read_entries(tmp_path, "shokubutsu", 40)


def test_sync_code_has_no_network_or_pixel_conversion():
    source = (ROOT / "scripts/sync_godot_assets.py").read_text(encoding="utf-8")
    for forbidden in ("requests.", "urllib.", "curl ", "wget ", "putalpha", "Image.open", "rmtree", "git clone"):
        assert forbidden not in source
