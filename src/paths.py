"""プロジェクト内のパス管理。"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "kinoko.json"
QUIZ_IMAGE_DIR = PROJECT_ROOT / "assets" / "images" / "quiz"
ZUKAN_IMAGE_DIR = PROJECT_ROOT / "assets" / "images" / "zukan"
SOUND_DIR = PROJECT_ROOT / "assets" / "sounds"
CORRECT_SOUND_PATH = SOUND_DIR / "correct_pingpong.wav"
WRONG_SOUND_PATH = SOUND_DIR / "wrong_buzz.wav"
