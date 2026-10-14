extends Control
## Mushroom-only, offline PC prototype using the already approved game data.

const CatalogModel = preload("res://scripts/KinokoCatalog.gd")
const QuizModel = preload("res://scripts/QuizSession.gd")
const CORRECT_SOUND_PATH := "res://assets/sounds/correct_pingpong.wav"
const PAGE_SIZE := 3
const BLACK := Color.BLACK
const CREAM := Color("fff8dc")
const ORANGE := Color("ffc46b")
const BLUE := Color("d5f1ff")
const GREEN := Color("d4f2d5")
const PURPLE := Color("e9dffc")

# Public state and controls also make the real scene easy to smoke-test.
var screen_name := ""
var catalog = CatalogModel.new()
var quiz_session = QuizModel.new()
var zukan_page := 0
var detail_key := ""
var choice_buttons: Array[Button] = []
var next_button: Button
var question_image: TextureRect
var feedback_label: Label
var explanation_label: Label
var sound_player: AudioStreamPlayer
var heading_label: Label
var result_label: Label
var hint_label: Label
var toxicity_hint_label: Label
var zukan_cards: Array[Button] = []
var zukan_prev_button: Button
var zukan_next_button: Button
var correct_sound_count := 0

var _screen_root: Control
var _feedback_panel: Panel
var _explanation_panel: Panel
var _quiz_generation := 0
var _pending_correct_sounds := 0


func _ready() -> void:
	_build_theme()
	# Keep sound outside the replaceable screen subtree so Next cannot cut it off.
	sound_player = AudioStreamPlayer.new()
	sound_player.name = "CorrectSound"
	sound_player.stream = load(CORRECT_SOUND_PATH)
	sound_player.finished.connect(_on_correct_sound_finished)
	add_child(sound_player)
	if not catalog.load_data():
		push_error(catalog.error_message)
		_show_data_error()
		return
	show_title()


func _build_theme() -> void:
	var japanese_font := SystemFont.new()
	japanese_font.font_names = PackedStringArray([
		"Hiragino Maru Gothic ProN", "Hiragino Sans",
		"Hiragino Kaku Gothic ProN", "Yu Gothic", "Noto Sans CJK JP", "Noto Sans JP",
	])
	japanese_font.font_weight = 600
	japanese_font.allow_system_fallback = true
	var game_theme := Theme.new()
	game_theme.default_font = japanese_font
	game_theme.default_font_size = 28
	game_theme.set_color("font_color", "Label", BLACK)
	for color_name in ["font_color", "font_hover_color", "font_pressed_color", "font_disabled_color", "font_focus_color"]:
		game_theme.set_color(color_name, "Button", BLACK)
	theme = game_theme


func show_title() -> void:
	_quiz_generation += 1
	_clear_screen("title")
	_add_label("きのこクイズ", Rect2(100, 92, 1080, 106), 68)
	_image(catalog.color_image_path("benitengutake"), Rect2(465, 218, 350, 245))
	_add_button("クイズで あそぶ", Rect2(390, 478, 500, 88), ORANGE, show_quiz_select, 36)
	_add_button("きのこ ずかん を みる", Rect2(390, 594, 500, 88), BLUE, show_zukan.bind(0), 34)


func show_quiz_select() -> void:
	_clear_screen("quiz_select")
	heading_label = _add_label("なんもん あそぶ？", Rect2(110, 112, 1060, 100), 56)
	_add_button("5もん", Rect2(330, 300, 620, 100), ORANGE, start_quiz.bind(5), 46)
	_add_button("10もん", Rect2(330, 438, 620, 100), GREEN, start_quiz.bind(10), 46)
	_add_button("タイトルへ もどる", Rect2(410, 662, 460, 72), PURPLE, show_title, 32)


func start_quiz(question_count: int) -> void:
	_quiz_generation += 1
	quiz_session = QuizModel.new()
	if not quiz_session.start(catalog.items, question_count):
		push_error(quiz_session.error_message)
		_show_data_error()
		return
	_show_question()


func _show_question() -> void:
	_clear_screen("quiz")
	var question: Dictionary = quiz_session.current_question()
	var item: Dictionary = question["answer"]
	heading_label = _add_label(quiz_session.progress_text(), Rect2(120, 23, 1040, 72), 46)
	var image_panel := _add_panel(Rect2(32, 112, 546, 342), Color.WHITE)
	question_image = _image(catalog.quiz_image_path(item["key"]), Rect2(12, 12, 522, 318), image_panel)
	question_image.name = "QuestionImage"
	var hints := _add_panel(Rect2(32, 469, 546, 284), BLUE)
	_add_label("どくの ヒント", Rect2(14, 9, 518, 43), 32, HORIZONTAL_ALIGNMENT_CENTER, hints)
	toxicity_hint_label = _add_label(catalog.toxicity_text(item), Rect2(14, 54, 518, 71), 32, HORIZONTAL_ALIGNMENT_CENTER, hints)
	_add_label("かたちの ヒント", Rect2(14, 127, 518, 43), 32, HORIZONTAL_ALIGNMENT_CENTER, hints)
	hint_label = _add_label(item["quiz_hint"], Rect2(14, 172, 518, 99), 32, HORIZONTAL_ALIGNMENT_CENTER, hints)
	for index in range(question["choices"].size()):
		var choice: Dictionary = question["choices"][index]
		var button := _add_button(choice["name"], Rect2(605, 112 + index * 76, 643, 66), ORANGE,
			select_answer.bind(choice["key"], quiz_session.current_index, _quiz_generation), 32)
		button.name = "Choice%d" % index
		choice_buttons.append(button)
	_feedback_panel = _add_panel(Rect2(605, 348, 643, 82), GREEN)
	feedback_label = _add_label("", Rect2(14, 7, 615, 68), 40, HORIZONTAL_ALIGNMENT_CENTER, _feedback_panel)
	feedback_label.name = "Feedback"
	_feedback_panel.visible = false
	next_button = _add_button("つぎへ", Rect2(605, 442, 643, 64), ORANGE,
		next_question.bind(quiz_session.current_index, _quiz_generation), 32)
	next_button.name = "NextQuestion"
	next_button.visible = false
	next_button.disabled = true
	_explanation_panel = _add_panel(Rect2(605, 520, 643, 192), Color.WHITE)
	var explanation_scroll := _scroll(Rect2(12, 10, 619, 172), _explanation_panel)
	explanation_label = _flow_label("", 26, explanation_scroll)
	explanation_label.name = "Explanation"
	_explanation_panel.visible = false
	_add_button("タイトルへ もどる", Rect2(605, 728, 643, 56), PURPLE, show_title, 32)


func select_answer(selected_key: String, expected_index: int = -1, expected_generation: int = -1) -> void:
	if screen_name != "quiz" or quiz_session.is_answered():
		return
	if expected_index >= 0 and expected_index != quiz_session.current_index:
		return
	if expected_generation >= 0 and expected_generation != _quiz_generation:
		return
	var result: Dictionary = quiz_session.answer(selected_key)
	if result.is_empty():
		return
	# Lock every choice synchronously before any new screen is drawn.
	for button in choice_buttons:
		button.disabled = true
	var item: Dictionary = result["answer"]
	question_image.texture = _texture(catalog.color_image_path(item["key"]))
	feedback_label.text = "せいかい！" if result["is_correct"] else "せいかいは %s" % item["name"]
	feedback_label.add_theme_font_size_override("font_size", 40 if result["is_correct"] else 34)
	_feedback_panel.visible = true
	explanation_label.text = _quiz_explanation(item)
	_explanation_panel.visible = true
	next_button.disabled = false
	next_button.visible = true
	if result["is_correct"]:
		_play_correct_sound()


func next_question(expected_index: int = -1, expected_generation: int = -1) -> void:
	if screen_name != "quiz" or not quiz_session.is_answered():
		return
	if expected_index >= 0 and expected_index != quiz_session.current_index:
		return
	if expected_generation >= 0 and expected_generation != _quiz_generation:
		return
	if quiz_session.next_question():
		_show_result()
	else:
		_show_question()


func _quiz_explanation(item: Dictionary) -> String:
	return "%s\nはえる ばしょ　%s\nみため　%s\n%s　%s" % [
		item["name"], item["habitat"], item["features"], catalog.toxicity_text(item), item["caution"],
	]


func _show_result() -> void:
	_clear_screen("result")
	heading_label = _add_label("けっか", Rect2(100, 95, 1080, 95), 64)
	result_label = _add_label("%dもん ちゅう %dもん せいかい！" % [
		quiz_session.total_questions(), quiz_session.correct_count,
	], Rect2(80, 266, 1120, 106), 52)
	if quiz_session.correct_count == quiz_session.total_questions():
		_add_label("これで きみも\nきのこ はかせだ！！", Rect2(60, 414, 1160, 150), 52)
	_add_button("タイトルへ もどる", Rect2(365, 658, 550, 84), PURPLE, show_title, 36)


func zukan_page_count() -> int:
	return int(ceil(float(catalog.items.size()) / PAGE_SIZE))


func show_zukan(page: int = 0) -> void:
	zukan_page = clampi(page, 0, maxi(0, zukan_page_count() - 1))
	_clear_screen("zukan")
	heading_label = _add_label("きのこ ずかん", Rect2(220, 18, 840, 68), 48)
	zukan_prev_button = _add_button("まえへ", Rect2(32, 102, 270, 64), BLUE, change_zukan_page.bind(-1), 32)
	zukan_prev_button.disabled = zukan_page == 0
	_add_label("%d / %d ページ" % [zukan_page + 1, zukan_page_count()], Rect2(322, 102, 636, 64), 32)
	zukan_next_button = _add_button("つぎへ", Rect2(978, 102, 270, 64), ORANGE, change_zukan_page.bind(1), 32)
	zukan_next_button.disabled = zukan_page >= zukan_page_count() - 1
	for index in range(PAGE_SIZE):
		var item_index := zukan_page * PAGE_SIZE + index
		if item_index >= catalog.items.size():
			break
		var item: Dictionary = catalog.items[item_index]
		var card := _add_button("", Rect2(32 + index * 416, 192, 384, 458), Color.WHITE,
			show_zukan_detail.bind(item["key"]), 32)
		card.name = "ZukanCard%d" % index
		card.tooltip_text = item["name"]
		var thumbnail := _image(catalog.color_image_path(item["key"]), Rect2(12, 14, 360, 326), card)
		thumbnail.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var name_label := _add_label(item["name"], Rect2(12, 346, 360, 96), 32, HORIZONTAL_ALIGNMENT_CENTER, card)
		name_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
		zukan_cards.append(card)
	_add_label("きのこを クリックしてね。", Rect2(260, 664, 760, 38), 26)
	_add_button("タイトルへ もどる", Rect2(390, 719, 500, 65), PURPLE, show_title, 32)


func change_zukan_page(offset: int) -> void:
	if screen_name != "zukan":
		return
	show_zukan(zukan_page + offset)


func show_zukan_detail(key: String) -> void:
	var item: Dictionary = catalog.get_item(key)
	if item.is_empty():
		return
	detail_key = key
	_clear_screen("zukan_detail")
	heading_label = _add_label(item["name"], Rect2(40, 14, 1200, 78), 48)
	var image_panel := _add_panel(Rect2(32, 112, 436, 580), Color.WHITE)
	question_image = _image(catalog.color_image_path(key), Rect2(12, 12, 412, 556), image_panel)
	var details_panel := _add_panel(Rect2(492, 112, 756, 580), Color.WHITE)
	var details_scroll := _scroll(Rect2(20, 16, 716, 548), details_panel)
	explanation_label = _flow_label(_detail_text(item), 28, details_scroll)
	explanation_label.name = "DetailText"
	_add_button("ずかんへ もどる", Rect2(175, 721, 450, 63), BLUE, show_zukan.bind(zukan_page), 32)
	_add_button("タイトルへ もどる", Rect2(655, 721, 450, 63), PURPLE, show_title, 32)


func _detail_text(item: Dictionary) -> String:
	var entries: Array[String] = [
		"はえる ばしょ\n%s" % item["habitat"],
		"みられる きせつ\n%s" % item["season"],
		"おおきさ\n%s" % item["size"],
		"いろ\n%s" % item["color"],
		"みため\n%s" % item["features"],
		"かたちの ヒント\n%s" % item["quiz_hint"],
		"どくのこと\n%s" % catalog.toxicity_text(item),
		"たべられる？\n%s" % _edibility_text(item),
		"きをつけること\n%s" % item["caution"],
		"にている きのこ\n%s" % item["similar_kinoko"],
	]
	if item["cooking"] != null:
		entries.append("りょうり\n%s" % item["cooking"])
	entries.append("まめちしき\n%s" % item["trivia"])
	return "\n\n".join(entries)


func _edibility_text(item: Dictionary) -> String:
	match item["edibility"]:
		"edible":
			return "たべられるよ。"
		"not_edible":
			return "たべられないよ。"
		_:
			return "たべられるか わかっていないよ。"


func _play_correct_sound() -> void:
	correct_sound_count += 1
	if sound_player.playing:
		_pending_correct_sounds += 1
	else:
		sound_player.play()


func _on_correct_sound_finished() -> void:
	if _pending_correct_sounds > 0:
		_pending_correct_sounds -= 1
		sound_player.play()


func _show_data_error() -> void:
	_clear_screen("error")
	_add_label("きのこデータが よめなかったよ。\nアプリを ひらきなおしてね。", Rect2(140, 220, 1000, 320), 40)


func _clear_screen(new_screen_name: String) -> void:
	if is_instance_valid(_screen_root):
		remove_child(_screen_root)
		_screen_root.queue_free()
	choice_buttons.clear()
	zukan_cards.clear()
	next_button = null
	question_image = null
	feedback_label = null
	explanation_label = null
	heading_label = null
	result_label = null
	hint_label = null
	toxicity_hint_label = null
	zukan_prev_button = null
	zukan_next_button = null
	_feedback_panel = null
	_explanation_panel = null
	screen_name = new_screen_name
	_screen_root = Control.new()
	_screen_root.name = "Screen"
	_screen_root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(_screen_root)
	var background := ColorRect.new()
	background.color = CREAM
	background.mouse_filter = Control.MOUSE_FILTER_IGNORE
	background.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_screen_root.add_child(background)


func _put(control: Control, rectangle: Rect2, parent: Control = null) -> void:
	(parent if parent != null else _screen_root).add_child(control)
	control.position = rectangle.position
	control.size = rectangle.size


func _add_label(text: String, rectangle: Rect2, font_size: int,
		alignment: HorizontalAlignment = HORIZONTAL_ALIGNMENT_CENTER, parent: Control = null) -> Label:
	var label := Label.new()
	label.text = text
	label.horizontal_alignment = alignment
	label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	label.add_theme_color_override("font_color", BLACK)
	label.add_theme_font_size_override("font_size", font_size)
	_put(label, rectangle, parent)
	return label


func _add_button(text: String, rectangle: Rect2, color: Color, callback: Callable,
		font_size: int = 32) -> Button:
	var button := Button.new()
	button.text = text
	button.add_theme_font_size_override("font_size", font_size)
	button.add_theme_stylebox_override("normal", _style(color))
	button.add_theme_stylebox_override("hover", _style(color.lightened(0.12)))
	button.add_theme_stylebox_override("pressed", _style(color.darkened(0.09)))
	button.add_theme_stylebox_override("disabled", _style(Color("e4e5de")))
	button.add_theme_stylebox_override("focus", _style(Color(0, 0, 0, 0), Color("227d9b"), 4))
	button.pressed.connect(callback)
	_put(button, rectangle)
	return button


func _add_panel(rectangle: Rect2, color: Color) -> Panel:
	var panel := Panel.new()
	panel.add_theme_stylebox_override("panel", _style(color, color.darkened(0.17), 2))
	_put(panel, rectangle)
	return panel


func _style(color: Color, border_color: Color = Color("bea16e"), border_width: int = 2) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = color
	style.border_color = border_color
	style.set_border_width_all(border_width)
	style.set_corner_radius_all(18)
	style.content_margin_left = 14
	style.content_margin_right = 14
	return style


func _texture(path: String) -> Texture2D:
	return load(path) as Texture2D


func _image(path: String, rectangle: Rect2, parent: Control = null) -> TextureRect:
	var image := TextureRect.new()
	image.texture = _texture(path)
	image.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	image.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	image.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_put(image, rectangle, parent)
	return image


func _scroll(rectangle: Rect2, parent: Control) -> ScrollContainer:
	var scroll := ScrollContainer.new()
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	scroll.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_AUTO
	_put(scroll, rectangle, parent)
	return scroll


func _flow_label(text: String, font_size: int, parent: ScrollContainer) -> Label:
	var label := Label.new()
	label.text = text
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	label.size_flags_vertical = Control.SIZE_EXPAND_FILL
	label.vertical_alignment = VERTICAL_ALIGNMENT_TOP
	label.add_theme_font_size_override("font_size", font_size)
	label.add_theme_color_override("font_color", BLACK)
	parent.add_child(label)
	return label
