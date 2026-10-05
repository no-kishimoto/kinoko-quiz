"""プロジェクト内のパス管理。"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "kinoko.json"
SHOKUBUTSU_DATA_PATH = PROJECT_ROOT / "data" / "shokubutsu.json"
KONCHUU_DATA_PATH = PROJECT_ROOT / "data" / "konchuu.json"
KYOURYUU_DATA_PATH = PROJECT_ROOT / "data" / "kyouryuu.json"
SHOKUBUTSU_QUIZ_IMAGE_DIR = PROJECT_ROOT / "assets" / "images" / "shokubutsu" / "quiz"
SHOKUBUTSU_ZUKAN_IMAGE_DIR = PROJECT_ROOT / "assets" / "images" / "shokubutsu" / "zukan"
KONCHUU_QUIZ_IMAGE_DIR = PROJECT_ROOT / "assets" / "images" / "konchuu" / "quiz"
KONCHUU_ZUKAN_IMAGE_DIR = PROJECT_ROOT / "assets" / "images" / "konchuu" / "zukan"
KYOURYUU_FOSSIL_IMAGE_DIR = PROJECT_ROOT / "assets" / "images" / "kyouryuu" / "fossil"
KYOURYUU_RECONSTRUCTION_IMAGE_DIR = PROJECT_ROOT / "assets" / "images" / "kyouryuu" / "reconstruction"
QUIZ_IMAGE_DIR = PROJECT_ROOT / "assets" / "images" / "quiz"
ZUKAN_IMAGE_DIR = PROJECT_ROOT / "assets" / "images" / "zukan"
SEARCH_BACKGROUND_DIR = PROJECT_ROOT / "assets" / "images" / "search" / "backgrounds"
SOUND_DIR = PROJECT_ROOT / "assets" / "sounds"
CORRECT_SOUND_PATH = SOUND_DIR / "correct_pingpong.wav"
INCORRECT_SOUND_PATH = SOUND_DIR / "incorrect_buzzer.wav"
