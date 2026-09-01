"""きのこクイズの起動入口。"""

from src.ui import APP_CSS, build_app


if __name__ == "__main__":
    build_app().launch(css=APP_CSS)
