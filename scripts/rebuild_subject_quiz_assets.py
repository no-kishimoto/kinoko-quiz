"""Rebuild plant/insect quiz PNGs without modifying the approved source alpha.

This never removes backgrounds or edits color source files. Internal gaps,
white petals, pale wings and antialiased edges all retain their source alpha.
"""

from __future__ import annotations

import argparse
import io
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data.subject_data import load_ready_subject_items
from scripts.remove_white_background import KONCHUU_HIGHLIGHTS, SHOKUBUTSU_HIGHLIGHTS
from src.images import create_quiz_image


def rebuild_subject_quiz_assets(
    subject: str,
    *,
    keys: tuple[str, ...] | None = None,
    check_only: bool = False,
    root: Path = ROOT,
) -> tuple[str, ...]:
    """Validate all selected inputs before replacing any quiz images.

    Returns keys whose quiz pixels differ. Unchanged files are left untouched.
    In check-only mode no directories or files are created.
    """
    if subject not in ("shokubutsu", "konchuu"):
        raise ValueError("subject must be shokubutsu or konchuu")
    items = load_ready_subject_items(root / "data" / f"{subject}.json")
    wanted = set(keys) if keys is not None else {item.key for item in items}
    unknown = wanted - {item.key for item in items}
    if unknown:
        raise ValueError("unknown keys: " + ", ".join(sorted(unknown)))
    highlights = SHOKUBUTSU_HIGHLIGHTS if subject == "shokubutsu" else KONCHUU_HIGHLIGHTS
    color_dir = root / "assets" / "images" / subject / "zukan"
    quiz_dir = root / "assets" / "images" / subject / "quiz"
    replacements: list[tuple[str, Path, bytes]] = []
    from PIL import Image

    for item in items:
        if item.key not in wanted:
            continue
        source_path = color_dir / item.image_filename
        destination = quiz_dir / item.image_filename
        if source_path.is_symlink() or destination.is_symlink():
            raise ValueError(f"symlink asset is not supported: {item.key}")
        with Image.open(source_path) as opened:
            source = opened.convert("RGBA")
        alpha = source.getchannel("A")
        corners = ((0, 0), (source.width - 1, 0), (0, source.height - 1),
                   (source.width - 1, source.height - 1))
        # Preserve imagegen's original alpha, including sub-visible 1/255
        # quantization noise. Do not threshold pale subject colors or alpha.
        if alpha.getextrema() != (0, 255) or any(alpha.getpixel(p) > 1 for p in corners):
            raise ValueError(f"source is not an approved transparent cutout: {item.key}")
        result = create_quiz_image(source, highlights[item.key])
        if result.getchannel("A").tobytes() != alpha.tobytes():
            raise ValueError(f"quiz generation changed source alpha: {item.key}")
        if destination.is_file():
            with Image.open(destination) as opened:
                existing = opened.convert("RGBA")
            if existing.size == result.size and existing.tobytes() == result.tobytes():
                continue
        buffer = io.BytesIO()
        result.save(buffer, format="PNG", optimize=True)
        replacements.append((item.key, destination, buffer.getvalue()))

    if not check_only and replacements:
        quiz_dir.mkdir(parents=True, exist_ok=True)
        # Stage every output first; no source image is ever a write target.
        with tempfile.TemporaryDirectory(prefix=".quiz-rebuild-", dir=quiz_dir) as temporary:
            staged = []
            for key, destination, content in replacements:
                path = Path(temporary) / f"{key}.png"
                path.write_bytes(content)
                staged.append((path, destination))
            for staged_path, destination in staged:
                os.replace(staged_path, destination)
    return tuple(key for key, _, _ in replacements)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--subject", required=True, choices=("shokubutsu", "konchuu"))
    parser.add_argument("--keys", nargs="+", help="Only regenerate these catalogue keys")
    parser.add_argument("--check", action="store_true", help="Report stale quizzes without writing")
    args = parser.parse_args(argv)
    try:
        changed = rebuild_subject_quiz_assets(args.subject, keys=tuple(args.keys) if args.keys else None,
                                             check_only=args.check)
    except (OSError, ValueError, KeyError) as exc:
        print(f"Quiz asset validation failed: {exc}", file=sys.stderr)
        return 1
    action = "Need rebuilding" if args.check else "Rebuilt"
    print(f"{action}: {len(changed)} {args.subject} quiz images. Source alpha left unchanged.")
    if changed:
        print(", ".join(changed))
    return 1 if args.check and changed else 0


if __name__ == "__main__":
    raise SystemExit(main())
