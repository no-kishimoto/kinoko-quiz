extends Control
## Mushroom-only, offline PC prototype using the already approved game data.

const CatalogModel = preload("res://scripts/KinokoCatalog.gd")
const QuizModel = preload("res://scripts/QuizSession.gd")
const CORRECT_SOUND_PATH := "res://assets/sounds/correct_pingpong.wav"
const PAGE_SIZE := 3
const BLACK := Color("000000")
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
var _feedback_panel: PanelContainer
var _explanation_panel: PanelContainer
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
	var page := _page()
	var content := _centered_column(page, 560, 20)
	heading_label = _label("きのこクイズ", 68, content, 560)
	var title_image := _image(catalog.color_image_path("benitengutake"), content)
	title_image.name = "TitleImage"
	title_image.custom_minimum_size.y = 250
	_button("クイズで あそぶ", ORANGE, show_quiz_select, content, 36, 88)
	_button("きのこ ずかん を みる", BLUE, show_zukan.bind(0), content, 34, 88)


func show_quiz_select() -> void:
	_clear_screen("quiz_select")
	var page := _page()
	var content := _centered_column(page, 640, 24)
	heading_label = _label("なんもん あそぶ？", 56, content, 640)
	_button("5もん", ORANGE, start_quiz.bind(5), content, 46, 100)
	_button("10もん", GREEN, start_quiz.bind(10), content, 46, 100)
	_button("タイトルへ もどる", PURPLE, show_title, content, 32, 72)


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
	var page := _page(14)
	heading_label = _label(quiz_session.progress_text(), 46, page, _content_width())
	var columns := _row(page, 24)
	columns.size_flags_vertical = Control.SIZE_EXPAND_FILL
	var left := _column(columns, 12)
	left.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	left.size_flags_stretch_ratio = 0.45
	var right := _column(columns, 12)
	right.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	right.size_flags_stretch_ratio = 0.55
	var left_width := (_content_width() - 24) * 0.45
	var right_width := (_content_width() - 24) * 0.55
	var image_panel := _panel(Color.WHITE, left)
	image_panel.size_flags_vertical = Control.SIZE_EXPAND_FILL
	image_panel.custom_minimum_size.y = 180
	question_image = _image(catalog.quiz_image_path(item["key"]), _padding(image_panel, 12))
	question_image.name = "QuestionImage"
	var hints := _column(_padding(_panel(BLUE, left), 12), 4)
	_label("どくの ヒント", 32, hints, left_width - 24)
	toxicity_hint_label = _label(catalog.toxicity_text(item), 32, hints, left_width - 24, true)
	_label("かたちの ヒント", 32, hints, left_width - 24)
	hint_label = _label(item["quiz_hint"], 32, hints, left_width - 24, true)
	var choices := _column(right, 10)
	for index in range(question["choices"].size()):
		var choice: Dictionary = question["choices"][index]
		var button := _button(choice["name"], ORANGE,
			select_answer.bind(choice["key"], quiz_session.current_index, _quiz_generation), choices, 32, 66)
		button.name = "Choice%d" % index
		choice_buttons.append(button)
	_feedback_panel = _panel(GREEN, right)
	feedback_label = _label("", 40, _padding(_feedback_panel, 10), right_width - 20, true)
	feedback_label.name = "Feedback"
	_feedback_panel.visible = false
	next_button = _button("つぎへ", ORANGE,
		next_question.bind(quiz_session.current_index, _quiz_generation), right, 32, 64)
	next_button.name = "NextQuestion"
	next_button.visible = false
	next_button.disabled = true
	_explanation_panel = _panel(Color.WHITE, right)
	_explanation_panel.size_flags_vertical = Control.SIZE_EXPAND_FILL
	var explanation_scroll := _scroll(_padding(_explanation_panel, 12))
	explanation_label = _label("", 26, explanation_scroll, right_width - 48, true, HORIZONTAL_ALIGNMENT_LEFT)
	explanation_label.vertical_alignment = VERTICAL_ALIGNMENT_TOP
	explanation_label.name = "Explanation"
	_explanation_panel.visible = false
	_footer("タイトルへ もどる", PURPLE, show_title, page, 560, 64, true)


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
	var page := _page()
	var content := _centered_column(page, 1080, 26)
	heading_label = _label("けっか", 64, content, 1080)
	result_label = _label("%dもん ちゅう %dもん せいかい！" % [
		quiz_session.total_questions(), quiz_session.correct_count,
	], 52, content, 1080, true)
	if quiz_session.correct_count == quiz_session.total_questions():
		_label("これで きみも\nきのこ はかせだ！！", 52, content, 1080)
	_footer("タイトルへ もどる", PURPLE, show_title, content, 560, 84)


func zukan_page_count() -> int:
	return int(ceil(float(catalog.items.size()) / PAGE_SIZE))


func show_zukan(page: int = 0) -> void:
	zukan_page = clampi(page, 0, maxi(0, zukan_page_count() - 1))
	_clear_screen("zukan")
	var layout := _page(16)
	heading_label = _label("きのこ ずかん", 48, layout, _content_width())
	var navigation := _row(layout, 18)
	zukan_prev_button = _button("まえへ", BLUE, change_zukan_page.bind(-1), navigation, 32, 64)
	zukan_prev_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	zukan_prev_button.disabled = zukan_page == 0
	var page_label := _label("%d / %d ページ" % [zukan_page + 1, zukan_page_count()], 32, navigation, 340)
	page_label.custom_minimum_size.x = 340
	zukan_next_button = _button("つぎへ", ORANGE, change_zukan_page.bind(1), navigation, 32, 64)
	zukan_next_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	zukan_next_button.disabled = zukan_page >= zukan_page_count() - 1
	var cards := _row(layout, 24)
	cards.size_flags_vertical = Control.SIZE_EXPAND_FILL
	for index in range(PAGE_SIZE):
		var item_index := zukan_page * PAGE_SIZE + index
		if item_index >= catalog.items.size():
			break
		var item: Dictionary = catalog.items[item_index]
		var card := _button("", Color.WHITE, show_zukan_detail.bind(item["key"]), cards)
		card.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		card.size_flags_vertical = Control.SIZE_EXPAND_FILL
		card.name = "ZukanCard%d" % index
		card.tooltip_text = item["name"]
		var card_padding := _padding(card, 12, true)
		var card_content := _column(card_padding, 12)
		card_content.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var thumbnail := _image(catalog.color_image_path(item["key"]), card_content)
		thumbnail.size_flags_vertical = Control.SIZE_EXPAND_FILL
		thumbnail.custom_minimum_size.y = 160
		_label(item["name"], 32, card_content, (_content_width() - 48) / 3 - 24, true)
		zukan_cards.append(card)
	_label("きのこを クリックしてね。", 26, layout, _content_width())
	_footer("タイトルへ もどる", PURPLE, show_title, layout, 520, 64)


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
	var page := _page(18)
	heading_label = _label(item["name"], 48, page, _content_width())
	var columns := _row(page, 24)
	columns.size_flags_vertical = Control.SIZE_EXPAND_FILL
	var image_panel := _panel(Color.WHITE, columns)
	image_panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	image_panel.size_flags_stretch_ratio = 0.38
	question_image = _image(catalog.color_image_path(key), _padding(image_panel, 12))
	var details_panel := _panel(Color.WHITE, columns)
	details_panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	details_panel.size_flags_stretch_ratio = 0.62
	var details_scroll := _scroll(_padding(details_panel, 16))
	explanation_label = _label(_detail_text(item), 28, details_scroll, (_content_width() - 24) * 0.62 - 52, true, HORIZONTAL_ALIGNMENT_LEFT)
	explanation_label.vertical_alignment = VERTICAL_ALIGNMENT_TOP
	explanation_label.name = "DetailText"
	var footer := _row(page, 24)
	_spacer(footer)
	_button("ずかんへ もどる", BLUE, show_zukan.bind(zukan_page), footer, 32, 64).custom_minimum_size.x = 450
	_button("タイトルへ もどる", PURPLE, show_title, footer, 32, 64).custom_minimum_size.x = 450
	_spacer(footer)


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
	var content := _centered_column(_page(), 1000, 16)
	_label("きのこデータが よめなかったよ。\nアプリを ひらきなおしてね。", 40, content, 1000, true)


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


func _content_width() -> float:
	return maxf(size.x, 1280) - 64


func _page(spacing: int = 18) -> VBoxContainer:
	var margin := _padding(_screen_root, 32, true)
	margin.add_theme_constant_override("margin_top", 24)
	margin.add_theme_constant_override("margin_bottom", 24)
	return _column(margin, spacing)


func _column(parent: Control, spacing: int = 12) -> VBoxContainer:
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", spacing)
	column.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	parent.add_child(column)
	return column


func _row(parent: Control, spacing: int = 18) -> HBoxContainer:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", spacing)
	row.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	parent.add_child(row)
	return row


func _padding(parent: Control, amount: int, full_rect: bool = false) -> MarginContainer:
	var padding := MarginContainer.new()
	for side in ["left", "right", "top", "bottom"]:
		padding.add_theme_constant_override("margin_%s" % side, amount)
	padding.mouse_filter = Control.MOUSE_FILTER_IGNORE
	if full_rect:
		padding.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	parent.add_child(padding)
	return padding


func _centered_column(parent: Control, width: float, spacing: int) -> VBoxContainer:
	var center := CenterContainer.new()
	center.size_flags_vertical = Control.SIZE_EXPAND_FILL
	parent.add_child(center)
	var content := _column(center, spacing)
	content.custom_minimum_size.x = width
	return content


func _spacer(parent: Control) -> Control:
	var spacer := Control.new()
	spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	spacer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	parent.add_child(spacer)
	return spacer


func _footer(text: String, color: Color, callback: Callable, parent: Control,
		width: float = 520, height: float = 64, align_right: bool = false) -> Button:
	var row := _row(parent, 0)
	_spacer(row)
	var button := _button(text, color, callback, row, 32, height)
	button.custom_minimum_size.x = width
	if not align_right:
		_spacer(row)
	return button


func _label(text: String, font_size: int, parent: Control, initial_width: float,
		wrap: bool = false, alignment: HorizontalAlignment = HORIZONTAL_ALIGNMENT_CENTER) -> Label:
	var label := Label.new()
	# Seed the available width BEFORE text, theme or parent-tree notifications.
	# A zero-width native CJK label can otherwise keep a one-character-per-line
	# minimum height and visually overlap unrelated images or buttons.
	label.size = Vector2(maxf(initial_width, 1), 1)
	label.theme = theme
	label.add_theme_font_size_override("font_size", font_size)
	label.add_theme_color_override("font_color", BLACK)
	label.horizontal_alignment = alignment
	label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART if wrap else TextServer.AUTOWRAP_OFF
	label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	label.size_flags_vertical = Control.SIZE_FILL
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	label.text = text
	parent.add_child(label)
	return label


func _button(text: String, color: Color, callback: Callable, parent: Control,
		font_size: int = 32, height: float = 64) -> Button:
	var button := Button.new()
	button.text = text
	button.custom_minimum_size.y = height
	button.add_theme_font_size_override("font_size", font_size)
	button.add_theme_stylebox_override("normal", _style(color))
	button.add_theme_stylebox_override("hover", _style(color.lightened(0.12)))
	button.add_theme_stylebox_override("pressed", _style(color.darkened(0.09)))
	button.add_theme_stylebox_override("disabled", _style(Color("e4e5de")))
	button.add_theme_stylebox_override("focus", _style(Color(0, 0, 0, 0), Color("227d9b"), 4))
	button.pressed.connect(callback)
	parent.add_child(button)
	return button


func _panel(color: Color, parent: Control) -> PanelContainer:
	var panel := PanelContainer.new()
	var panel_style := _style(color, color.darkened(0.17), 2)
	panel_style.content_margin_left = 0
	panel_style.content_margin_right = 0
	panel_style.content_margin_top = 0
	panel_style.content_margin_bottom = 0
	panel.add_theme_stylebox_override("panel", panel_style)
	parent.add_child(panel)
	return panel


func _style(color: Color, border_color: Color = Color("bea16e"), border_width: int = 2) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = color
	style.border_color = border_color
	style.set_border_width_all(border_width)
	style.set_corner_radius_all(18)
	style.content_margin_left = 14
	style.content_margin_right = 14
	style.content_margin_top = 6
	style.content_margin_bottom = 6
	return style


func _texture(path: String) -> Texture2D:
	return load(path) as Texture2D


func _image(path: String, parent: Control) -> TextureRect:
	var image := TextureRect.new()
	image.texture = _texture(path)
	image.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	image.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	image.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	image.size_flags_vertical = Control.SIZE_EXPAND_FILL
	image.mouse_filter = Control.MOUSE_FILTER_IGNORE
	parent.add_child(image)
	return image


func _scroll(parent: Control) -> ScrollContainer:
	var scroll := ScrollContainer.new()
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	scroll.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_AUTO
	scroll.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	parent.add_child(scroll)
	return scroll
