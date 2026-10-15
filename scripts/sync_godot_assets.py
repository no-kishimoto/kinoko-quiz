"""Prepare all approved game resources for an entirely offline Godot game.

This developer-only step copies original bytes. It never modifies transparency,
downloads resources, deletes files, or changes the Gradio source catalogue.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.sync_godot_kinoko import (  # noqa: E402
    AssetSyncError,
    KEY_PATTERN,
    MANIFEST_PATH as LEGACY_MANIFEST_PATH,
    _checksum,
    _safe_destination,
    _write_atomic,
    sync_assets as sync_mushroom_assets,
)
from src.dinosaur_search import load_dinosaur_search_assets  # noqa: E402


CATALOG_PATH = Path("data/game_catalog.json")
MANIFEST_PATH = Path("assets/game_manifest.json")
SUBJECTS = {
    "kinoko": ("きのこ", 30),
    "shokubutsu": ("しょくぶつ", 40),
    "konchuu": ("こんちゅう", 29),
    "kyouryuu": ("きょうりゅう", 18),
}


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _bytes_checksum(data: bytes) -> dict[str, Any]:
    return {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}


def _read_entries(repo_root: Path, subject: str, expected: int) -> list[dict[str, Any]]:
    path = repo_root / f"data/{subject}.json"
    try:
        entries = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AssetSyncError(f"Could not read data/{subject}.json") from exc
    if not isinstance(entries, list) or len(entries) != expected:
        raise AssetSyncError(f"The {subject} catalogue must contain exactly {expected} entries")
    keys, names = set(), set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise AssetSyncError(f"Each {subject} entry must be an object")
        key, name = entry.get("key"), entry.get("name")
        if not isinstance(key, str) or not KEY_PATTERN.fullmatch(key) or key in keys:
            raise AssetSyncError(f"{subject} keys must be valid and unique")
        if not isinstance(name, str) or not name.strip() or name in names:
            raise AssetSyncError(f"{subject} names must be nonempty and unique")
        for field in (("quiz_hint", "features") if subject == "kinoko" else ("quiz_hint", "zukan_text")):
            if not isinstance(entry.get(field), str) or not entry[field].strip():
                raise AssetSyncError(f"{subject} {key} needs {field}")
        keys.add(key)
        names.add(name)
    return entries


def _plan(repo_root: Path) -> tuple[dict[str, Any], list[Path]]:
    """Resolve the complete approved plan before creating any destination."""
    paths: set[Path] = {Path("assets/sounds/correct_pingpong.wav")}

    def resource(path: Path | str) -> str:
        path = Path(path)
        if path.is_absolute():
            try:
                path = path.relative_to(repo_root)
            except ValueError as exc:
                raise AssetSyncError("Source resource must be inside the repository") from exc
        source = repo_root / path
        if not source.resolve().is_relative_to(repo_root):
            raise AssetSyncError(f"Source resource escapes the repository: {path}")
        if not source.is_file():
            raise AssetSyncError(f"Missing source asset: {path}")
        paths.add(path)
        return "res://" + path.as_posix()

    forest_dir = repo_root / "assets/images/search/backgrounds"
    forests = [resource(path) for path in sorted(forest_dir.glob("*.png"))]
    if len(forests) != 4:
        raise AssetSyncError("The approved forest backgrounds must contain exactly four images")
    # Independent approval records, not filename existence, determine which
    # dinosaur search specimens and reconstructions may enter the game.
    try:
        dinosaur_assets = load_dinosaur_search_assets(repo_root)
    except (OSError, ValueError, KeyError) as exc:
        raise AssetSyncError(f"Dinosaur assets are not fully approved: {exc}") from exc
    if not dinosaur_assets.reconstruction_ready:
        raise AssetSyncError("All eighteen dinosaur reconstructions need independent approval")
    overrides_path = repo_root / "assets/images/kyouryuu/review/transparent/review-overrides.json"
    try:
        approved_descriptions = json.loads(overrides_path.read_text(encoding="utf-8"))["items"]
    except (OSError, ValueError, KeyError) as exc:
        raise AssetSyncError("Could not read the approved dinosaur descriptions") from exc
    description_overrides = {}
    for entry in approved_descriptions:
        if entry.get("description_status") != "approved":
            raise AssetSyncError("Dinosaur description needs independent approval")
        key = entry.get("key")
        if key in description_overrides or key not in dinosaur_assets.specimen_images:
            raise AssetSyncError("Dinosaur description keys must be approved and unique")
        if any(not isinstance(entry.get(field), str) or not entry[field].strip()
               for field in ("name", "quiz_hint", "zukan_text")):
            raise AssetSyncError("Approved dinosaur descriptions must be complete")
        description_overrides[key] = entry
    if len(description_overrides) != 10:
        raise AssetSyncError("The original ten dinosaur descriptions need approval")

    subjects: dict[str, Any] = {}
    for subject, (label, count) in SUBJECTS.items():
        entries = _read_entries(repo_root, subject, count)
        resource(f"data/{subject}.json")
        items = []
        for original in entries:
            item = dict(original)
            key = item["key"]
            if subject == "kinoko":
                quiz_folder, color_folder = "quiz", "zukan"
            elif subject == "kyouryuu":
                quiz_folder, color_folder = "kyouryuu/fossil", "kyouryuu/reconstruction"
            else:
                quiz_folder, color_folder = f"{subject}/quiz", f"{subject}/zukan"
            item["quiz_image"] = resource(f"assets/images/{quiz_folder}/{key}.png")
            item["color_image"] = resource(f"assets/images/{color_folder}/{key}.png")
            item["search_image"] = item["color_image"]
            if subject == "kyouryuu":
                item["fossil_image"] = resource(dinosaur_assets.specimen_images[key])
                item["search_image"] = resource(dinosaur_assets.reconstruction_images[key])
                # Reviewed transparent variants supersede the older canonical
                # pairs in every Godot mode, without changing those originals.
                item["quiz_image"] = item["fossil_image"]
                item["color_image"] = item["search_image"]
                if key in description_overrides:
                    approved = description_overrides[key]
                    if approved["name"] != item["name"]:
                        raise AssetSyncError("Approved dinosaur description name does not match")
                    item.update({field: approved[field] for field in ("quiz_hint", "zukan_text")})
            items.append(item)
        subjects[subject] = {"label": label, "items": items, "backgrounds": forests}
        if subject == "kyouryuu":
            living = {
                habitat: [resource(path) for path in backgrounds]
                for habitat, backgrounds in dinosaur_assets.living_backgrounds.items()
            }
            subjects[subject].update(
                backgrounds=[path for group in living.values() for path in group],
                fossil_backgrounds=[resource(path) for path in dinosaur_assets.backgrounds],
                habitats=dict(dinosaur_assets.habitats),
                habitat_backgrounds=living,
            )
    # Ensure even the fixed sound path receives the same source preflight.
    resource("assets/sounds/correct_pingpong.wav")
    catalog = {"format_version": 1, "species_count": 117, "subjects": subjects}
    return catalog, sorted(paths)


def sync_assets(repo_root: Path = ROOT, *, check_only: bool = False) -> dict[str, Any]:
    """Copy or verify all four subject catalogues and unmodified approved media.

    All source and destination paths are checked before the first write. A
    checksum manifest includes the generated catalogue, and repeated runs leave
    matching files and unrelated user files untouched.
    """
    repo_root = Path(repo_root).resolve()
    godot_root = repo_root / "godot"
    if godot_root.is_symlink():
        raise AssetSyncError("The Godot project root must not be a symbolic link")
    catalog, paths = _plan(repo_root)
    destinations = {path: _safe_destination(godot_root, path) for path in paths}
    catalog_destination = _safe_destination(godot_root, CATALOG_PATH)
    manifest_destination = _safe_destination(godot_root, MANIFEST_PATH)
    _safe_destination(godot_root, LEGACY_MANIFEST_PATH)
    checksums = {path.as_posix(): _checksum(repo_root / path) for path in paths}
    catalog_bytes = _json_bytes(catalog)
    checksums[CATALOG_PATH.as_posix()] = _bytes_checksum(catalog_bytes)
    manifest = {"format_version": 1, "species_count": 117, "files": checksums}
    manifest_bytes = _json_bytes(manifest)
    mismatches = [
        path for path in paths
        if not destinations[path].is_file() or _checksum(destinations[path]) != checksums[path.as_posix()]
    ]
    catalog_matches = catalog_destination.is_file() and catalog_destination.read_bytes() == catalog_bytes
    manifest_matches = manifest_destination.is_file() and manifest_destination.read_bytes() == manifest_bytes
    if check_only:
        if mismatches or not catalog_matches or not manifest_matches:
            names = [path.as_posix() for path in mismatches]
            if not catalog_matches:
                names.append(CATALOG_PATH.as_posix())
            if not manifest_matches:
                names.append(MANIFEST_PATH.as_posix())
            raise AssetSyncError("Godot assets need synchronization: " + ", ".join(names))
        sync_mushroom_assets(repo_root, check_only=True)
        return manifest
    # Retain the established mushroom preparation contract and its manifest.
    # The full plan and all legacy destinations have already passed preflight.
    sync_mushroom_assets(repo_root)
    for path in mismatches:
        data = (repo_root / path).read_bytes()
        if _bytes_checksum(data) != checksums[path.as_posix()]:
            raise AssetSyncError(f"Source changed during synchronization: {path}")
        _write_atomic(destinations[path], data)
    if not catalog_matches:
        _write_atomic(catalog_destination, catalog_bytes)
    if not manifest_matches:
        _write_atomic(manifest_destination, manifest_bytes)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify only; do not modify files")
    args = parser.parse_args()
    try:
        manifest = sync_assets(check_only=args.check)
    except (AssetSyncError, OSError) as exc:
        print(f"Godot asset preparation failed: {exc}", file=sys.stderr)
        return 1
    print(f"{'Verified' if args.check else 'Prepared'} 4 subjects, 117 species and {len(manifest['files'])} resources for Godot.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
