"""Copy approved mushroom assets into Godot, unchanged and without networking.

This is a developer preparation step, not a dependency of the running game.
Only the canonical 30-species JSON, 60 PNGs and correct sound are copied.
Unrelated destination files are never removed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = Path("assets/kinoko_manifest.json")
EXPECTED_COUNT = 30
KEY_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


class AssetSyncError(ValueError):
    """The source catalogue, assets or destination is unsafe or incomplete."""


def _source_paths(repo_root: Path) -> list[Path]:
    data_path = repo_root / "data/kinoko.json"
    try:
        entries = json.loads(data_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AssetSyncError("Could not read data/kinoko.json") from exc
    if not isinstance(entries, list) or len(entries) != EXPECTED_COUNT:
        raise AssetSyncError("The mushroom catalogue must contain exactly 30 entries")
    keys: set[str] = set()
    names: set[str] = set()
    paths = [Path("data/kinoko.json")]
    for entry in entries:
        if not isinstance(entry, dict):
            raise AssetSyncError("Each mushroom entry must be an object")
        key, name = entry.get("key"), entry.get("name")
        if not isinstance(key, str) or not KEY_PATTERN.fullmatch(key) or key in keys:
            raise AssetSyncError("Mushroom keys must be valid and unique")
        if not isinstance(name, str) or not name.strip() or name in names:
            raise AssetSyncError("Mushroom names must be nonempty and unique")
        keys.add(key)
        names.add(name)
        paths.extend(Path(f"assets/images/{folder}/{key}.png") for folder in ("quiz", "zukan"))
    paths.append(Path("assets/sounds/correct_pingpong.wav"))
    missing = [str(path) for path in paths if not (repo_root / path).is_file()]
    if missing:
        raise AssetSyncError("Missing source assets: " + ", ".join(missing))
    return paths


def _checksum(path: Path) -> dict[str, Any]:
    digest = hashlib.sha256()
    byte_count = 0
    with path.open("rb") as source:
        while block := source.read(1024 * 1024):
            digest.update(block)
            byte_count += len(block)
    return {"sha256": digest.hexdigest(), "bytes": byte_count}


def _safe_destination(godot_root: Path, relative: Path) -> Path:
    destination = godot_root / relative
    if not destination.resolve().is_relative_to(godot_root.resolve()):
        raise AssetSyncError(f"Destination escapes the Godot project: {relative}")
    if destination.is_symlink():
        raise AssetSyncError(f"Destination must not be a symbolic link: {relative}")
    return destination


def _write_atomic(destination: Path, data: bytes) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=destination.parent, prefix=".kinoko-sync-", delete=False) as temporary:
        temporary_path = Path(temporary.name)
        try:
            temporary.write(data)
            temporary.flush()
            os.fsync(temporary.fileno())
        except BaseException:
            temporary_path.unlink(missing_ok=True)
            raise
    try:
        os.replace(temporary_path, destination)
    finally:
        temporary_path.unlink(missing_ok=True)


def sync_assets(repo_root: Path = ROOT, *, check_only: bool = False) -> dict[str, Any]:
    """Synchronize known resources or verify them, preserving other files.

    Preflight every input and destination before changing anything. Files with
    matching hashes and an identical manifest are reused on subsequent runs.
    """

    repo_root = Path(repo_root).resolve()
    godot_root = repo_root / "godot"
    paths = _source_paths(repo_root)
    # Check all destinations before the first copy; no recursive deletion occurs.
    destinations = {path: _safe_destination(godot_root, path) for path in paths}
    manifest_destination = _safe_destination(godot_root, MANIFEST_PATH)
    checksums = {path.as_posix(): _checksum(repo_root / path) for path in paths}
    manifest = {"format_version": 1, "species_count": EXPECTED_COUNT, "files": checksums}
    manifest_bytes = (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    mismatches = [
        path for path in paths
        if not destinations[path].is_file() or _checksum(destinations[path]) != checksums[path.as_posix()]
    ]
    manifest_matches = manifest_destination.is_file() and manifest_destination.read_bytes() == manifest_bytes
    if check_only:
        if mismatches or not manifest_matches:
            names = [path.as_posix() for path in mismatches]
            if not manifest_matches:
                names.append(MANIFEST_PATH.as_posix())
            raise AssetSyncError("Godot assets need synchronization: " + ", ".join(names))
        return manifest
    for path in mismatches:
        data = (repo_root / path).read_bytes()
        if hashlib.sha256(data).hexdigest() != checksums[path.as_posix()]["sha256"]:
            raise AssetSyncError(f"Source changed during synchronization: {path}")
        _write_atomic(destinations[path], data)
    if not manifest_matches:
        _write_atomic(manifest_destination, manifest_bytes)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify only; do not copy or modify files")
    args = parser.parse_args()
    try:
        manifest = sync_assets(check_only=args.check)
    except (AssetSyncError, OSError) as exc:
        print(f"Godot asset preparation failed: {exc}", file=sys.stderr)
        return 1
    action = "Verified" if args.check else "Prepared"
    print(f"{action} {manifest['species_count']} mushrooms and {len(manifest['files'])} resources for Godot.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
