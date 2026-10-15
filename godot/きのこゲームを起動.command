#!/bin/bash
# Local launcher only. No installation, download, remote connection or deletion.
set -euo pipefail

godot_preview_root="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)"
godot_preview_repo="$(CDPATH= cd -- "$godot_preview_root/.." && pwd -P)"
godot_preview_bin=""
godot_preview_import_needed=false
godot_preview_ready_marker="$godot_preview_root/.godot/full-assets-imported"

for godot_preview_candidate in \
  "${GODOT_BIN:-}" \
  "/Applications/Godot.app/Contents/MacOS/Godot" \
  "$HOME/Applications/Godot.app/Contents/MacOS/Godot" \
  "$HOME/Downloads/Godot.app/Contents/MacOS/Godot" \
  "$godot_preview_root/../../../../../tools/godot-4.7.2/Godot.app/Contents/MacOS/Godot"; do
  if [[ -n "$godot_preview_candidate" && -x "$godot_preview_candidate" ]]; then
    godot_preview_bin="$godot_preview_candidate"
    break
  fi
done
if [[ -z "$godot_preview_bin" ]] && command -v godot >/dev/null 2>&1; then
  godot_preview_bin="$(command -v godot)"
fi
if [[ -z "$godot_preview_bin" ]]; then
  printf '%s\n' 'Godotが見つかりません。DockのGodotでproject.godotをインポートし、F5で実行してください。'
  read -r -p 'Returnでとじます。' godot_preview_reply
  exit 1
fi

# Synchronization is preparation only; all resources remain original byte copies.
if [[ -x "$godot_preview_repo/.venv/bin/python" ]]; then
  if ! "$godot_preview_repo/.venv/bin/python" -B "$godot_preview_repo/scripts/sync_godot_assets.py" --check >/dev/null; then
    "$godot_preview_repo/.venv/bin/python" -B "$godot_preview_repo/scripts/sync_godot_assets.py"
    godot_preview_import_needed=true
  fi
elif [[ ! -f "$godot_preview_root/data/game_catalog.json" || ! -f "$godot_preview_root/assets/game_manifest.json" || ! -f "$godot_preview_root/assets/sounds/correct_pingpong.wav" ]]; then
  if command -v python3 >/dev/null 2>&1; then
    python3 -B "$godot_preview_repo/scripts/sync_godot_assets.py"
    godot_preview_import_needed=true
  else
    printf '%s\n' '素材の準備が必要です。godot/README.mdの「素材の準備」を確認してください。'
    read -r -p 'Returnでとじます。' godot_preview_reply
    exit 1
  fi
fi

cd -- "$godot_preview_root"
if [[ "$godot_preview_import_needed" == true || ! -f "$godot_preview_ready_marker" || "$godot_preview_root/assets/game_manifest.json" -nt "$godot_preview_ready_marker" ]] || ! compgen -G "$godot_preview_root/.godot/imported/*.ctex" >/dev/null; then
  # Prepare a fresh project or reimport updated source images/sound.
  # A partial cache is not ready: mark it only after a successful full import.
  # Invalidate an older success stamp even if a repaired asset left the full
  # manifest unchanged. An interrupted repair must also retry on next launch.
  if [[ -f "$godot_preview_ready_marker" ]]; then
    touch -t 197001010000 "$godot_preview_ready_marker"
  fi
  "$godot_preview_bin" --headless --editor --path "$godot_preview_root" --import
  mkdir -p "$godot_preview_root/.godot"
  touch "$godot_preview_ready_marker"
fi
printf '%s\n' '4つの なかまの ゲームを きどうします。ゲームを とじると おわります。'
exec "$godot_preview_bin" --path "$godot_preview_root"
