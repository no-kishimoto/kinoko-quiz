"""プロジェクト内のパス管理。"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "kinoko.json"
SHOKUBUTSU_DATA_PATH = PROJECT_ROOT / "data" / "shokubutsu.json"
KONCHUU_DATA_PATH = PROJECT_ROOT / "data" / "konchuu.json"
SHOKUBUTSU_QUIZ_IMAGE_DIR = PROJECT_ROOT / "assets" / "images" / "shokubutsu" / "quiz"
SHOKUBUTSU_ZUKAN_IMAGE_DIR = PROJECT_ROOT / "assets" / "images" / "shokubutsu" / "zukan"
QUIZ_IMAGE_DIR = PROJECT_ROOT / "assets" / "images" / "quiz"
ZUKAN_IMAGE_DIR = PROJECT_ROOT / "assets" / "images" / "zukan"
SEARCH_BACKGROUND_DIR = PROJECT_ROOT / "assets" / "images" / "search" / "backgrounds"
SOUND_DIR = PROJECT_ROOT / "assets" / "sounds"
CORRECT_SOUND_PATH = SOUND_DIR / "correct_pingpong.wav"
WRONG_SOUND_PATH = SOUND_DIR / "wrong_buzz.wav"
