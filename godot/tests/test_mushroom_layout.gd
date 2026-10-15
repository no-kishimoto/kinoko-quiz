extends SceneTree
## Exercise the actual scene at PC aspect ratios, including every approved name.
## Child labels intentionally inside card buttons and scrollable text are not
## treated as unrelated overlapping UI; the scroll viewport itself is checked.

const MainScene = preload("res://scenes/Main.tscn")
const CANVASES := [Vector2i(1280, 800), Vector2i(1366, 768), Vector2i(1600, 900), Vector2i(1920, 1080)]
const TOLERANCE := 2.0

var checks := 0
var failures: Array[String] = []
var app: Control
var viewport: SubViewport
var context := ""
var worst_font_height := 0.0
var widest_name := 0.0


func _initialize() -> void:
	call_deferred("_run")


func _check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		var detail := "%s: %s" % [context, message]
		failures.append(detail)
		# Keep a genuine failing baseline readable while still reporting its count.
		if failures.size() <= 35:
			push_error(detail)


func _frames() -> void:
	await process_frame
	await process_frame
	await process_frame


func _controls(node: Node, result: Array[Control]) -> void:
	if node is Control and not node.is_visible_in_tree():
		return
	if node is Label or node is Button or node is ScrollContainer or node is TextureRect:
		result.append(node as Control)
	for child in node.get_children():
		_controls(child, result)


func _inside_scroll(node: Node) -> bool:
	return _nearest_scroll(node) != null


func _nearest_scroll(node: Node) -> ScrollContainer:
	var parent := node.get_parent()
	while parent != null and parent != app:
		if parent is ScrollContainer:
			return parent as ScrollContainer
		parent = parent.get_parent()
	return null


func _contains(outer: Rect2, inner: Rect2) -> bool:
	return outer.grow(TOLERANCE).encloses(inner)


func _intersects(a: Rect2, b: Rect2) -> bool:
	# Round-off, a shared boundary, and a focus outline are not text collisions.
	return a.grow(-TOLERANCE).intersects(b.grow(-TOLERANCE))


func _label_height(label: Label) -> float:
	var font := label.get_theme_font("font")
	var font_size := label.get_theme_font_size("font_size")
	var line_height := font.get_height(font_size)
	worst_font_height = maxf(worst_font_height, line_height)
	return line_height * label.get_line_count() + max(0, label.get_line_count() - 1) * label.get_theme_constant("line_spacing")


func _check_screen() -> void:
	var controls: Array[Control] = []
	_controls(app, controls)
	var canvas := Rect2(Vector2.ZERO, Vector2(viewport.size))
	for control in controls:
		if _inside_scroll(control):
			# The long, approved encyclopedia explanation is clipped by a scroller.
			# It may extend vertically, but text must still wrap to the visible width.
			var scroll := _nearest_scroll(control)
			_check(control.size.x <= scroll.size.x + TOLERANCE,
				"Scrollable explanation requires horizontal clipping: %s" % control.name)
			if control is Label and not control.text.is_empty():
				_check(_label_height(control) <= control.size.y + TOLERANCE,
					"Scroll text control does not hold every rendered line: %s" % control.name)
			continue
		var rect := control.get_global_rect()
		_check(_contains(canvas, rect), "Visible control outside viewport: %s %s" % [control.name, rect])
		var parent := control.get_parent()
		if parent is Control:
			_check(_contains(parent.get_global_rect(), rect), "Control exceeds its layout parent: %s" % control.name)
		if control is Label and not control.text.is_empty():
			_check(_label_height(control) <= control.size.y + TOLERANCE,
				"Rendered label is clipped: %s (%d lines; needs %.1f, has %.1f)" % [control.text, control.get_line_count(), _label_height(control), control.size.y])
		if control is Button:
			_check(control.size.x + TOLERANCE >= control.get_combined_minimum_size().x
				and control.size.y + TOLERANCE >= control.get_combined_minimum_size().y,
				"Button is smaller than its text/font/style minimum: %s" % control.text)
	for index in range(controls.size()):
		var first := controls[index]
		if _inside_scroll(first):
			continue
		for other_index in range(index + 1, controls.size()):
			var second := controls[other_index]
			if _inside_scroll(second) or first.is_ancestor_of(second) or second.is_ancestor_of(first):
				continue
			# Two unrelated text/button/image/scroll regions must not cover each other.
			_check(not _intersects(first.get_global_rect(), second.get_global_rect()),
				"Unrelated UI regions overlap: %s / %s" % [first.name, second.name])


func _force_question(item: Dictionary, item_index: int) -> String:
	var choices: Array[Dictionary] = [item,
		app.catalog.items[(item_index + 1) % app.catalog.items.size()],
		app.catalog.items[(item_index + 2) % app.catalog.items.size()]]
	var questions: Array[Dictionary] = [{"answer": item, "choices": choices}]
	app.quiz_session.questions = questions
	app.quiz_session.current_index = 0
	app.quiz_session.correct_count = 0
	app.quiz_session.current_result = {}
	app._show_question()
	return choices[1]["key"]


func _check_quiz_fonts() -> void:
	var next_size: int = app.next_button.get_theme_font_size("font_size")
	_check(next_size == 32, "Next retains approved large 32px font")
	_check(app.hint_label.get_theme_font_size("font_size") == next_size, "Shape hint matches Next font")
	_check(app.toxicity_hint_label.get_theme_font_size("font_size") == next_size, "Toxicity hint matches Next font")
	for button in app.choice_buttons:
		_check(button.get_theme_font_size("font_size") == next_size, "Choice matches Next font")


func _check_quiz_answer_layout() -> void:
	var feedback: Rect2 = app.feedback_label.get_global_rect()
	var next_rect: Rect2 = app.next_button.get_global_rect()
	_check(feedback.end.y <= next_rect.position.y + TOLERANCE, "Next appears below, not under feedback")
	_check(next_rect.position.y - feedback.end.y <= 42, "Next remains immediately below feedback")
	_check(next_rect.end.y <= app.explanation_label.get_global_rect().position.y + TOLERANCE,
		"Explanation starts after Next instead of covering it")


func _run() -> void:
	viewport = SubViewport.new()
	viewport.name = "LayoutViewport"
	viewport.size = CANVASES[0]
	viewport.gui_disable_input = true
	root.add_child(viewport)
	app = MainScene.instantiate()
	viewport.add_child(app)
	await _frames()
	_check(app.catalog.items.size() == 30, "All 30 approved mushrooms loaded")
	var initial_controls: Array[Control] = []
	_controls(app, initial_controls)
	for node in initial_controls:
		if node is Label and node.text == "きのこクイズ":
			print("Title label startup rect: %s" % node.get_global_rect())
		if node is TextureRect:
			print("Title image startup rect: %s" % node.get_global_rect())
	for dimensions in CANVASES:
		viewport.size = dimensions
		await _frames()
		context = "%dx%d title" % [dimensions.x, dimensions.y]
		app.show_title()
		await _frames()
		_check_screen()
		context = "%dx%d count" % [dimensions.x, dimensions.y]
		app.show_quiz_select()
		await _frames()
		_check_screen()
		for item_index in range(app.catalog.items.size()):
			var item: Dictionary = app.catalog.items[item_index]
			context = "%dx%d quiz %s" % [dimensions.x, dimensions.y, item["key"]]
			var wrong_key := _force_question(item, item_index)
			await _frames()
			_check(app.hint_label.text == item["quiz_hint"], "Approved hint remains unchanged")
			_check(app.toxicity_hint_label.text == app.catalog.toxicity_text(item), "Approved toxicity remains unchanged")
			_check_quiz_fonts()
			_check_screen()
			widest_name = maxf(widest_name, app.feedback_label.get_theme_font("font").get_string_size(
				"せいかいは %s" % item["name"], HORIZONTAL_ALIGNMENT_LEFT, -1, 34).x)
			app.select_answer(wrong_key)
			await _frames()
			context += " incorrect feedback"
			_check(app.feedback_label.text == "せいかいは %s" % item["name"], "Full correct name remains unchanged")
			_check_quiz_answer_layout()
			_check_screen()
			context = "%dx%d detail %s" % [dimensions.x, dimensions.y, item["key"]]
			app.show_zukan_detail(item["key"])
			await _frames()
			_check_screen()
		for page in range(app.zukan_page_count()):
			context = "%dx%d encyclopedia %d" % [dimensions.x, dimensions.y, page + 1]
			app.show_zukan(page)
			await _frames()
			_check(app.zukan_cards.size() == 3, "Exactly three cards in one row")
			_check_screen()
			for card_index in range(app.zukan_cards.size() - 1):
				var first: Rect2 = app.zukan_cards[card_index].get_global_rect()
				var second: Rect2 = app.zukan_cards[card_index + 1].get_global_rect()
				_check(absf(first.position.y - second.position.y) < TOLERANCE
					and first.end.x <= second.position.x + TOLERANCE, "Encyclopedia cards stay horizontally separated")
		context = "%dx%d results" % [dimensions.x, dimensions.y]
		app.start_quiz(5)
		app.quiz_session.correct_count = 5
		app._show_result()
		await _frames()
		_check_screen()
		app.quiz_session.correct_count = 2
		app._show_result()
		await _frames()
		_check_screen()
	app.sound_player.stop()
	app.sound_player.stream = null
	await create_timer(0.1).timeout
	viewport.queue_free()
	await _frames()
	print("Font metrics: max rendered line height %.1fpx; longest incorrect-answer text %.1fpx at34px." % [worst_font_height, widest_name])
	if failures.is_empty():
		print("PASS: responsive PC layout; all30 hints/names/details,10 pages,4 viewport sizes (%d checks)." % checks)
		quit(0)
	else:
		printerr("FAIL: %d of %d actual-scene layout checks." % [failures.size(), checks])
		quit(1)
