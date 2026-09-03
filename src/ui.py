"""Gradio Blocksによるクイズ画面。"""

import base64
import random
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from data.kinoko_data import Kinoko, load_kinoko, validate_image_assets
from src.paths import (
    CORRECT_SOUND_PATH,
    DATA_PATH,
    QUIZ_IMAGE_DIR,
    SEARCH_BACKGROUND_DIR,
    WRONG_SOUND_PATH,
    ZUKAN_IMAGE_DIR,
)
from src.quiz import QuizSession, create_quiz_session
from src.math_game import AdditionSession, create_addition_session
from src.search import SearchSession, create_search_session, prompt_text, render_scene, status_text
from src.zukan import zukan_detail_text, zukan_page

APP_CSS = """
.gradio-container { background: #fff8dc; font-family: sans-serif; }
.main-title { text-align: center; color: #000000 !important; font-size: 3rem; }
.main-title * { color: #000000 !important; }
.center-text { text-align: center; color: #000000 !important; }
.center-text * { color: #000000 !important; }
.result-text, .result-text * {
    color: #000000 !important;
    font-size: 2.15rem !important;
    font-weight: 800 !important;
    line-height: 1.55 !important;
}
.result-text h1, .result-text h2, .result-text h3 {
    font-size: 2.65rem !important;
}
.progress-text, .progress-text * {
    font-size: 1.9rem !important;
    font-weight: 800 !important;
    margin: 0 !important;
}
.quiz-layout { align-items: stretch; }
.quiz-left, .quiz-right { gap: 12px !important; }
.quiz-image { max-height: 330px !important; }
.hint-card {
    background: #e7f7ff;
    border: 4px solid #43a5d5;
    border-radius: 20px;
    color: #000000 !important;
    padding: 8px 16px;
    font-size: 1.55rem !important;
}
.hint-card * { color: #000000 !important; }
.hint-card h3 { font-size: 1.8rem !important; margin: 0 0 2px !important; }
.hint-card p { margin: 0 0 8px !important; }
.hint-card p:last-child { margin-bottom: 0 !important; }
.big-feedback {
    background: #ffffff !important;
    border: 6px solid #ff9f1c !important;
    border-radius: 24px !important;
    color: #c1121f !important;
    font-size: 2.3rem !important;
    font-weight: 800 !important;
    padding: 22px !important;
    text-align: center !important;
}
.big-feedback * { color: #c1121f !important; }
.choice button { min-height: 64px; font-size: 1.65rem !important; }
.main-button { min-height: 64px; font-size: 1.5rem !important; }
.explanation-card { font-size: 1.3rem; line-height: 1.45; }
.sound-effect {
    height: 1px !important;
    width: 1px !important;
    left: -9999px !important;
    opacity: 0 !important;
    overflow: hidden !important;
    pointer-events: none !important;
    position: absolute !important;
}
.sound-effect audio { height: 1px !important; width: 1px !important; }
.zukan-card { background: #ffffff; border: 3px solid #43a5d5; border-radius: 18px; padding: 10px; }
.zukan-card button { min-height: 56px; font-size: 1.35rem !important; }
.zukan-screen { margin: 0 auto; max-width: 1200px; }
.zukan-grid { flex-wrap: nowrap !important; }
.zukan-image { max-height: 200px !important; }
.zukan-nav button { min-height: 58px; font-size: 1.2rem !important; }
.detail-screen { margin: 0 auto; max-width: 1200px; }
.detail-content { align-items: flex-start; }
.zukan-detail-image { max-height: 420px !important; }
.detail-info {
    background: #ffffff;
    border: 3px solid #43a5d5;
    border-radius: 18px;
    color: #000000 !important;
    font-size: 1.15rem !important;
    line-height: 1.4 !important;
    padding: 12px 20px;
}
.detail-info * { color: #000000 !important; }
.detail-info h3 { color: #e85d04 !important; font-size: 1.35rem !important; margin: 8px 0 2px !important; }
.detail-info p { margin: 0 0 10px !important; }
.search-screen { margin: 0 auto; max-width: 1120px; }
.search-layout { align-items: center; }
.search-scene { cursor: crosshair !important; }
.search-targets {
    background: #e7f7ff;
    border: 4px solid #43a5d5;
    border-radius: 20px;
    color: #000000 !important;
    font-size: 1.35rem !important;
    padding: 10px 18px;
}
.search-targets * { color: #000000 !important; }
.search-status { min-height: 88px; }
.math-equation, .math-equation * { font-size: 3.2rem !important; font-weight: 800 !important; color: #000000 !important; text-align: center; }
.math-mushrooms, .math-mushrooms * { font-size: 3rem !important; line-height: 1.5 !important; text-align: center; }
@media (min-width: 900px) {
    .quiz-screen { max-height: calc(100vh - 32px); overflow: hidden; }
}
"""


@dataclass(frozen=True)
class QuestionView:
    """画面へ渡す、現在の1問分の表示内容。"""

    progress: str
    image: str
    hint: str
    choices: tuple[str, str, str]


def toxicity_text(item: Kinoko) -> str:
    """データ値を子ども向け表示へ変換する。"""

    return {
        "poisonous": "どくあり",
        "non_poisonous": "どくなし",
        "unknown": "どくが あるか わかっていない",
    }[item.toxicity]


def question_view(session: QuizSession, quiz_image_dir: Path = QUIZ_IMAGE_DIR) -> QuestionView:
    """回答前の問題表示を作る。"""

    question = session.current_question
    return QuestionView(
        progress=session.progress_text,
        image=str(quiz_image_dir / question.answer.image_filename),
        hint=(
            f"### どくの ヒント\n{toxicity_text(question.answer)} だよ。\n\n"
            f"### かたちの ヒント\n{question.answer.quiz_hint}。"
        ),
        choices=tuple(choice.name for choice in question.choices),
    )


def explanation_text(item: Kinoko) -> str:
    """回答後の短い解説を作る。"""

    return (
        f"### {item.name}\n\n"
        f"**はえる ばしょ**　{item.habitat}\n\n"
        f"**みため**　{item.features}\n\n"
        f"**{toxicity_text(item)}**　{item.caution}"
    )


def result_text(session: QuizSession) -> str:
    """最後の結果だけを表示する。"""

    text = (
        "# けっか\n\n"
        f"ぜんぶで {session.total_questions}もん\n\n"
        f"せいかいは {session.correct_count}もん"
    )
    if session.correct_count == session.total_questions:
        text += "\n\n## これで きみも きのこ はかせだ！！"
    return text


def sound_html(sound_path: Path, nonce: int) -> str:
    """再生バーを作らず、回答ごとに新しい音声要素を返す。"""

    encoded = base64.b64encode(sound_path.read_bytes()).decode("ascii")
    return (
        '<audio autoplay preload="auto" '
        f'src="data:audio/wav;base64,{encoded}#play-{nonce}"></audio>'
    )


def build_app():
    """全画面と画面遷移を組み立てる。"""

    try:
        import gradio as gr
    except ImportError as exc:  # 起動時にだけ外部依存を必要とする
        raise RuntimeError("gradio is required to run the app") from exc

    kinoko = load_kinoko(DATA_PATH)
    validate_image_assets(kinoko, ZUKAN_IMAGE_DIR)
    validate_image_assets(kinoko, QUIZ_IMAGE_DIR)
    search_backgrounds = tuple(sorted(SEARCH_BACKGROUND_DIR.glob("*.png")))
    if len(search_backgrounds) < 3:
        raise RuntimeError("at least three search background assets are required")
    for sound_path in (CORRECT_SOUND_PATH, WRONG_SOUND_PATH):
        if not sound_path.is_file():
            raise RuntimeError(f"missing sound asset: {sound_path}")

    with gr.Blocks(title="きのこクイズ") as app:
        session_state = gr.State(value=None)
        math_state = gr.State(value=None)
        zukan_page_state = gr.State(value=0)
        search_state = gr.State(value=None)

        with gr.Column(visible=True) as title_screen:
            gr.Markdown("# 🍄 きのこクイズ", elem_classes="main-title")
            quiz_start = gr.Button("クイズで あそぶ", variant="primary", elem_classes="main-button")
            math_start = gr.Button("たしざんで あそぶ", variant="primary", elem_classes="main-button")
            search_start = gr.Button("きのこ さがし", variant="primary", elem_classes="main-button")
            zukan_start = gr.Button("きのこ ずかん を みる", elem_classes="main-button")

        with gr.Column(visible=False) as count_screen:
            gr.Markdown("# なんもん あそぶ？", elem_classes="center-text")
            five_button = gr.Button("5もん", variant="primary", elem_classes="main-button")
            ten_button = gr.Button("10もん", variant="primary", elem_classes="main-button")

        with gr.Column(visible=False, elem_classes="quiz-screen") as quiz_screen:
            progress = gr.Markdown(elem_classes=["center-text", "progress-text"])
            with gr.Row(elem_classes="quiz-layout"):
                with gr.Column(scale=1, elem_classes="quiz-left"):
                    image = gr.Image(
                        show_label=False,
                        interactive=False,
                        height=330,
                        elem_classes="quiz-image",
                    )
                    hint = gr.Markdown(elem_classes=["center-text", "hint-card"])
                with gr.Column(scale=1, elem_classes="quiz-right"):
                    choice_buttons = [
                        gr.Button("", elem_classes="choice") for _ in range(3)
                    ]
                    feedback = gr.HTML(visible=False, elem_classes="big-feedback")
                    next_button = gr.Button(
                        "つぎへ",
                        visible=False,
                        variant="primary",
                        elem_classes="main-button",
                    )
                    explanation = gr.Markdown(visible=False, elem_classes="explanation-card")
                    quiz_title_button = gr.Button("タイトルへ もどる", elem_classes="main-button")
            sound = gr.HTML(value="", elem_classes="sound-effect")

        with gr.Column(visible=False, elem_classes="quiz-screen") as math_screen:
            math_progress = gr.Markdown(elem_classes=["center-text", "progress-text"])
            math_equation = gr.Markdown(elem_classes="math-equation")
            math_mushrooms = gr.Markdown(elem_classes="math-mushrooms")
            math_choice_buttons = [gr.Button("", elem_classes="choice") for _ in range(3)]
            math_feedback = gr.HTML(visible=False, elem_classes="big-feedback")
            math_next_button = gr.Button("つぎへ", visible=False, variant="primary", elem_classes="main-button")

        with gr.Column(visible=False, elem_classes="zukan-screen") as zukan_screen:
            gr.Markdown("# きのこ ずかん", elem_classes="main-title")
            with gr.Row(elem_classes="zukan-nav"):
                zukan_previous = gr.Button("まえへ", interactive=False, elem_classes="main-button")
                zukan_page_text = gr.Markdown(elem_classes=["center-text", "progress-text"])
                zukan_next = gr.Button("つぎへ", interactive=False, elem_classes="main-button")
            card_images = []
            card_buttons = []
            with gr.Row(elem_classes="zukan-grid"):
                for _ in range(3):
                    with gr.Column(scale=1, min_width=0, elem_classes="zukan-card"):
                        card_images.append(
                            gr.Image(
                                show_label=False,
                                interactive=False,
                                visible=False,
                                height=200,
                                elem_classes="zukan-image",
                            )
                        )
                        card_buttons.append(gr.Button("", visible=False))
            zukan_title_button = gr.Button("タイトルへ もどる", elem_classes="main-button")

        with gr.Column(visible=False, elem_classes="detail-screen") as detail_screen:
            detail_name = gr.Markdown(elem_classes="main-title")
            with gr.Row(elem_classes="detail-content"):
                with gr.Column(scale=1):
                    detail_image = gr.Image(
                        show_label=False,
                        interactive=False,
                        elem_classes="zukan-detail-image",
                    )
                with gr.Column(scale=1):
                    detail_text = gr.Markdown(elem_classes="detail-info")
            zukan_back_button = gr.Button("ずかんへ もどる", elem_classes="main-button")

        with gr.Column(visible=False, elem_classes="search-screen") as search_screen:
            gr.Markdown("# きのこ さがし", elem_classes="main-title")
            search_prompt = gr.Markdown(elem_classes="center-text")
            search_status = gr.Markdown(elem_classes=["center-text", "search-status"])
            with gr.Row(elem_classes="search-layout"):
                with gr.Column(scale=3):
                    search_scene = gr.Image(
                        show_label=False,
                        interactive=True,
                        sources=None,
                        buttons=[],
                        height=600,
                        elem_classes="search-scene",
                    )
                with gr.Column(scale=1):
                    search_next_button = gr.Button("つぎの もんだい", visible=False, variant="primary", elem_classes="main-button")
                    search_title_button = gr.Button("タイトルへ もどる", elem_classes="main-button")

        with gr.Column(visible=False) as result_screen:
            result = gr.Markdown(elem_classes=["center-text", "result-text"])
            title_button = gr.Button("タイトルへ もどる", variant="primary", elem_classes="main-button")

        def show_count_screen():
            return {
                title_screen: gr.Column(visible=False),
                count_screen: gr.Column(visible=True),
            }

        quiz_start.click(
            show_count_screen,
            outputs=[title_screen, count_screen],
        )

        def math_mushrooms_text(session: AdditionSession) -> str:
            if not session.shows_mushrooms:
                return ""
            question = session.question
            return f"🍄 " * question.left + "＋　" + f"🍄 " * question.right

        def start_math():
            session = create_addition_session()
            question = session.question
            updates = {
                math_state: session,
                title_screen: gr.Column(visible=False),
                math_screen: gr.Column(visible=True),
                math_progress: session.progress_text,
                math_equation: f"# {question.left} ＋ {question.right} ＝ ？",
                math_mushrooms: gr.Markdown(
                    value=math_mushrooms_text(session), visible=session.shows_mushrooms
                ),
                math_feedback: gr.HTML(value="", visible=False),
                math_next_button: gr.Button(visible=False),
                sound: None,
            }
            updates.update({button: gr.Button(value=str(value), interactive=True) for button, value in zip(math_choice_buttons, question.choices)})
            return updates

        math_start.click(
            start_math,
            outputs=[math_state, title_screen, math_screen, math_progress, math_equation, math_mushrooms, *math_choice_buttons, math_feedback, math_next_button, sound],
        )

        def answer_math(session: AdditionSession | None, choice_index: int):
            if session is None:
                raise gr.Error("たしざんを はじめてね")
            updated = deepcopy(session)
            correct = updated.answer(updated.question.choices[choice_index])
            message = "せいかい！" if correct else f"せいかいは {updated.question.answer}"
            sound_path = CORRECT_SOUND_PATH if correct else WRONG_SOUND_PATH
            updates = {
                math_state: updated,
                math_feedback: gr.HTML(value=f"<div>{message}</div>", visible=True),
                math_next_button: gr.Button(visible=True),
                sound: sound_html(sound_path, updated.current_index + 1000),
            }
            updates.update({button: gr.Button(interactive=False) for button in math_choice_buttons})
            return updates

        for index, button in enumerate(math_choice_buttons):
            button.click(
                lambda session, index=index: answer_math(session, index),
                inputs=math_state,
                outputs=[math_state, *math_choice_buttons, math_feedback, math_next_button, sound],
            )

        def next_math(session: AdditionSession | None):
            if session is None:
                raise gr.Error("たしざんを はじめてね")
            updated = deepcopy(session)
            if updated.next_question():
                return {
                    math_state: updated,
                    math_screen: gr.Column(visible=False),
                    result_screen: gr.Column(visible=True),
                    result: f"# たしざんの けっか\n\nぜんぶで 5もん\n\nせいかいは {updated.correct_count}もん",
                }
            question = updated.question
            updates = {
                math_state: updated,
                math_progress: updated.progress_text,
                math_equation: f"# {question.left} ＋ {question.right} ＝ ？",
                math_mushrooms: gr.Markdown(
                    value=math_mushrooms_text(updated), visible=updated.shows_mushrooms
                ),
                math_feedback: gr.HTML(value="", visible=False),
                math_next_button: gr.Button(visible=False),
                sound: None,
            }
            updates.update({button: gr.Button(value=str(value), interactive=True) for button, value in zip(math_choice_buttons, question.choices)})
            return updates

        math_next_button.click(
            next_math,
            inputs=math_state,
            outputs=[math_state, math_screen, result_screen, result, math_progress, math_equation, math_mushrooms, *math_choice_buttons, math_feedback, math_next_button, sound],
        )

        def start_search():
            session = create_search_session(kinoko, search_backgrounds)
            return {
                search_state: session,
                title_screen: gr.Column(visible=False),
                search_screen: gr.Column(visible=True),
                search_scene: render_scene(session, ZUKAN_IMAGE_DIR),
                search_prompt: prompt_text(session),
                search_status: status_text(session),
                search_next_button: gr.Button(visible=False),
            }

        search_start.click(
            start_search,
            outputs=[
                search_state, title_screen, search_screen, search_scene,
                search_prompt, search_status, search_next_button,
            ],
        )

        def search_click(session: SearchSession | None, evt: gr.SelectData):
            if session is None:
                raise gr.Error("きのこ さがしを はじめてね")
            index = evt.index
            if not isinstance(index, (tuple, list)) or len(index) != 2:
                return {
                    search_state: session,
                    search_status: "## きのこを クリックしてね。",
                }
            with Image.open(session.background_path) as scene:
                width, height = scene.size
            updated = deepcopy(session)
            found = updated.choose_at(index[0] / width, index[1] / height)
            return {
                search_state: updated,
                search_scene: render_scene(updated, ZUKAN_IMAGE_DIR),
                search_status: status_text(updated, clicked=True),
                search_next_button: gr.Button(visible=found),
                sound: sound_html(CORRECT_SOUND_PATH, random.randint(1, 999999)) if found else None,
            }

        search_scene.select(
            search_click,
            inputs=search_state,
            outputs=[search_state, search_scene, search_status, search_next_button, sound],
        )

        search_next_button.click(
            start_search,
            outputs=[search_state, title_screen, search_screen, search_scene, search_prompt, search_status, search_next_button],
        )

        def search_to_title():
            return {
                search_state: None,
                search_screen: gr.Column(visible=False),
                title_screen: gr.Column(visible=True),
            }

        search_title_button.click(
            search_to_title,
            outputs=[search_state, search_screen, title_screen],
        )

        def start_quiz(count: int):
            session = create_quiz_session(kinoko, count)
            view = question_view(session)
            updates = {
                session_state: session,
                count_screen: gr.Column(visible=False),
                quiz_screen: gr.Column(visible=True),
                progress: view.progress,
                image: view.image,
                hint: view.hint,
                feedback: gr.HTML(value="", visible=False),
                explanation: gr.Markdown(value="", visible=False),
                sound: None,
                next_button: gr.Button(visible=False),
            }
            updates.update({
                button: gr.Button(value=name, interactive=True)
                for button, name in zip(choice_buttons, view.choices)
            })
            return updates

        start_outputs = [
            session_state, count_screen, quiz_screen, progress, image, hint,
            *choice_buttons, feedback, explanation, sound, next_button,
        ]
        five_button.click(lambda: start_quiz(5), outputs=start_outputs)
        ten_button.click(lambda: start_quiz(10), outputs=start_outputs)

        def quiz_to_title():
            return {
                session_state: None,
                quiz_screen: gr.Column(visible=False),
                title_screen: gr.Column(visible=True),
            }

        quiz_title_button.click(
            quiz_to_title,
            outputs=[session_state, quiz_screen, title_screen],
        )

        def show_zukan(index: int):
            page = zukan_page(kinoko, index)
            updates = {
                zukan_page_state: page.index,
                title_screen: gr.Column(visible=False),
                zukan_screen: gr.Column(visible=True),
                zukan_page_text: page.page_text,
                zukan_previous: gr.Button(interactive=page.has_previous),
                zukan_next: gr.Button(interactive=page.has_next),
            }
            for slot, image_component in enumerate(card_images):
                if slot < len(page.items):
                    item = page.items[slot]
                    updates[image_component] = gr.Image(
                        value=str(ZUKAN_IMAGE_DIR / item.image_filename), visible=True
                    )
                    updates[card_buttons[slot]] = gr.Button(value=item.name, visible=True)
                else:
                    updates[image_component] = gr.Image(value=None, visible=False)
                    updates[card_buttons[slot]] = gr.Button(value="", visible=False)
            return updates

        zukan_outputs = [
            zukan_page_state, title_screen, zukan_screen, zukan_page_text,
            *card_images, *card_buttons, zukan_previous, zukan_next,
        ]
        zukan_start.click(lambda: show_zukan(0), outputs=zukan_outputs)
        zukan_previous.click(
            lambda index: show_zukan(index - 1),
            inputs=zukan_page_state,
            outputs=zukan_outputs,
        )
        zukan_next.click(
            lambda index: show_zukan(index + 1),
            inputs=zukan_page_state,
            outputs=zukan_outputs,
        )

        def show_detail(page_index: int, slot: int):
            page = zukan_page(kinoko, page_index)
            if slot >= len(page.items):
                raise gr.Error("きのこを えらんでね")
            item = page.items[slot]
            return {
                zukan_screen: gr.Column(visible=False),
                detail_screen: gr.Column(visible=True),
                detail_name: f"# {item.name}",
                detail_image: str(ZUKAN_IMAGE_DIR / item.image_filename),
                detail_text: zukan_detail_text(item, toxicity_text(item)),
            }

        detail_outputs = [zukan_screen, detail_screen, detail_name, detail_image, detail_text]
        for slot, button in enumerate(card_buttons):
            button.click(
                lambda index, slot=slot: show_detail(index, slot),
                inputs=zukan_page_state,
                outputs=detail_outputs,
            )

        def back_to_zukan(index: int):
            updates = show_zukan(index)
            updates[detail_screen] = gr.Column(visible=False)
            return updates

        zukan_back_button.click(
            back_to_zukan,
            inputs=zukan_page_state,
            outputs=[*zukan_outputs, detail_screen],
        )

        def zukan_to_title():
            return {
                zukan_page_state: 0,
                zukan_screen: gr.Column(visible=False),
                title_screen: gr.Column(visible=True),
            }

        zukan_title_button.click(
            zukan_to_title,
            outputs=[zukan_page_state, zukan_screen, title_screen],
        )

        def answer(session: QuizSession | None, choice_index: int):
            if session is None:
                raise gr.Error("クイズを はじめてね")
            updated = deepcopy(session)
            question = updated.current_question
            selected = question.choices[choice_index]
            answer_result = updated.answer(selected.key)
            answer_item = answer_result.answer
            message = (
                "せいかい！"
                if answer_result.is_correct
                else f"せいかいは {answer_item.name}"
            )
            sound_path = CORRECT_SOUND_PATH if answer_result.is_correct else WRONG_SOUND_PATH
            updates = {
                session_state: updated,
                image: str(ZUKAN_IMAGE_DIR / answer_item.image_filename),
                feedback: gr.HTML(value=f"<div>{message}</div>", visible=True),
                explanation: gr.Markdown(value=explanation_text(answer_item), visible=True),
                sound: sound_html(sound_path, updated.current_index),
                next_button: gr.Button(visible=True),
            }
            updates.update({button: gr.Button(interactive=False) for button in choice_buttons})
            return updates

        answer_outputs = [
            session_state, image, *choice_buttons, feedback, explanation, sound,
            next_button,
        ]
        for index, button in enumerate(choice_buttons):
            button.click(
                lambda session, index=index: answer(session, index),
                inputs=session_state,
                outputs=answer_outputs,
            )

        def go_next(session: QuizSession | None):
            if session is None:
                raise gr.Error("クイズを はじめてね")
            updated = deepcopy(session)
            finished = updated.next_question()
            if finished:
                return {
                    session_state: updated,
                    quiz_screen: gr.Column(visible=False),
                    result_screen: gr.Column(visible=True),
                    result: result_text(updated),
                }
            view = question_view(updated)
            updates = {
                session_state: updated,
                progress: view.progress,
                image: view.image,
                hint: view.hint,
                feedback: gr.HTML(value="", visible=False),
                explanation: gr.Markdown(value="", visible=False),
                sound: None,
                next_button: gr.Button(visible=False),
            }
            updates.update({
                button: gr.Button(value=name, interactive=True)
                for button, name in zip(choice_buttons, view.choices)
            })
            return updates

        next_outputs = [
            session_state, quiz_screen, result_screen, result, progress, image,
            hint, *choice_buttons, feedback, explanation, sound, next_button,
        ]
        next_button.click(go_next, inputs=session_state, outputs=next_outputs)

        def return_to_title():
            return {
                session_state: None,
                math_state: None,
                result_screen: gr.Column(visible=False),
                title_screen: gr.Column(visible=True),
            }

        title_button.click(
            return_to_title,
            outputs=[session_state, math_state, result_screen, title_screen],
        )

    return app
