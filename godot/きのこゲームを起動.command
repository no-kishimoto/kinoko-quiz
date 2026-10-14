#!/bin/bash
# Local launcher only. No installation, download, remote connection or deletion.
set -euo pipefail

godot_preview_root="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)"
godot_preview_repo="$(CDPATH= cd -- "$godot_preview_root/.." && pwd -P)"
godot_preview_bin=""
godot_preview_import_needed=false

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
  if ! "$godot_preview_repo/.venv/bin/python" -B "$godot_preview_repo/scripts/sync_godot_kinoko.py" --check >/dev/null; then
    "$godot_preview_repo/.venv/bin/python" -B "$godot_preview_repo/scripts/sync_godot_kinoko.py"
    godot_preview_import_needed=true
  fi
elif [[ ! -f "$godot_preview_root/data/kinoko.json" || ! -f "$godot_preview_root/assets/sounds/correct_pingpong.wav" ]]; then
  if command -v python3 >/dev/null 2>&1; then
    python3 -B "$godot_preview_repo/scripts/sync_godot_kinoko.py"
    godot_preview_import_needed=true
  else
    printf '%s\n' '素材の準備が必要です。godot/README.mdの「素材の準備」を確認してください。'
    read -r -p 'Returnでとじます。' godot_preview_reply
    exit 1
  fi
fi

cd -- "$godot_preview_root"
if [[ "$godot_preview_import_needed" == true ]] || ! compgen -G "$godot_preview_root/.godot/imported/*.ctex" >/dev/null; then
  # Prepare a fresh project or reimport updated source images/sound.
  "$godot_preview_bin" --headless --editor --path "$godot_preview_root" --import
fi
printf '%s\n' 'きのこクイズを きどうします。ゲームを とじると おわります。'
exec "$godot_preview_bin" --path "$godot_preview_root"
