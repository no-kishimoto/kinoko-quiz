extends SceneTree
## Integration checks use the real scene and approved assets, not mock widgets.
## Run after asset synchronization/import with --headless --script this file.

const MainScene = preload("res://scenes/Main.tscn")
const SUBJECTS := {"kinoko": 30, "shokubutsu": 40, "konchuu": 29, "kyouryuu": 18}
const CANVASES := [Vector2i(1280, 800), Vector2i(1366, 768), Vector2i(1600, 900), Vector2i(1920, 1080)]
const TOLERANCE := 2.0

var app: Control
var viewport: SubViewport
var checks := 0
var failures: Array[String] = []
var context := "startup"
var kanji := RegEx.new()
var sound_id := 0
var detail_count := 0


func _initialize() -> void:
	call_deferred("_run")


func _check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		var detail := "%s: %s" % [context, message]
		failures.append(detail)
		if failures.size() <= 45:
			push_error(detail)


func _frames() -> void:
	await process_frame
	await process_frame
	await process_frame


func _visible_text(node: Node) -> String:
	if node is Control and not node.is_visible_in_tree():
		return ""
	var text := ""
	if node is Label or node is Button:
		text += node.text + "\n"
	for child in node.get_children():
		text += _visible_text(child)
	return text


func _controls(node: Node, result: Array[Control]) -> void:
	if node is Control and not node.is_visible_in_tree():
		return
	if node is Label or node is Button or node is TextureRect or node is ScrollContainer or node == app.search_board:
		result.append(node as Control)
	for child in node.get_children():
		_controls(child, result)


func _nearest_scroll(node: Node) -> ScrollContainer:
	var parent := node.get_parent()
	while parent != null and parent != app:
		if parent is ScrollContainer:
			return parent as ScrollContainer
		parent = parent.get_parent()
	return null


func _label_height(label: Label) -> float:
	var font := label.get_theme_font("font")
	var font_size := label.get_theme_font_size("font_size")
	return font.get_height(font_size) * label.get_line_count() + maxi(0, label.get_line_count() - 1) * label.get_theme_constant("line_spacing")


func _intersects(first: Rect2, second: Rect2) -> bool:
	# A collapsed label is still diagnosed by bounds/height checks, but shrinking
	# a sub4px rectangle would itself cause a native Rect2 diagnostic flood.
	if minf(first.size.x, first.size.y) <= 2 * TOLERANCE or minf(second.size.x, second.size.y) <= 2 * TOLERANCE:
		return false
	return first.grow(-TOLERANCE).intersects(second.grow(-TOLERANCE))


func _check_screen(allow_kanji: bool = false) -> void:
	if not allow_kanji:
		_check(kanji.search(_visible_text(app)) == null, "Only kana, numbers and symbols outside the late arithmetic stage")
	var controls: Array[Control] = []
	_controls(app, controls)
	var canvas := Rect2(Vector2.ZERO, Vector2(viewport.size))
	for control in controls:
		if control is Button or control is Label:
			_check(control.get_theme_color("font_color") == Color.BLACK, "Text remains black: %s" % control.name)
		var scroll := _nearest_scroll(control)
		if scroll != null:
			_check(control.size.x <= scroll.size.x + TOLERANCE, "Long explanation wraps inside its scroll viewport")
			if control is Label and not control.text.is_empty():
				_check(_label_height(control) <= control.size.y + TOLERANCE, "Scrollable text has sufficient height")
			continue
		var rect := control.get_global_rect()
		_check(canvas.grow(TOLERANCE).encloses(rect), "Visible control stays in the PC canvas: %s %s" % [control.name, rect])
		if control.get_parent() is Control:
			_check(control.get_parent().get_global_rect().grow(TOLERANCE).encloses(rect), "Control stays inside its layout parent: %s" % control.name)
		if control is Label and not control.text.is_empty():
			_check(_label_height(control) <= control.size.y + TOLERANCE, "Every line of label fits: %s" % control.text)
		if control is Button:
			_check(control.size.x + TOLERANCE >= control.get_combined_minimum_size().x and control.size.y + TOLERANCE >= control.get_combined_minimum_size().y, "Button is large enough for its label: %s" % control.text)
	for index in range(controls.size()):
		var first := controls[index]
		if _nearest_scroll(first) != null:
			continue
		for other_index in range(index + 1, controls.size()):
			var second := controls[other_index]
			if _nearest_scroll(second) != null or first.is_ancestor_of(second) or second.is_ancestor_of(first):
				continue
			_check(not _intersects(first.get_global_rect(), second.get_global_rect()), "Unrelated UI regions do not overlap: %s / %s" % [first.name, second.name])
	_check(app.sound_player.get_instance_id() == sound_id, "One sound player survives every screen change")


func _wrong_quiz_key(question: Dictionary) -> String:
	for choice in question["choices"]:
		if choice["key"] != question["answer"]["key"]:
			return choice["key"]
	return ""


func _check_answer_layout() -> void:
	_check(app.next_button.visible and not app.next_button.disabled, "Manual Next appears after an answer")
	var feedback: Rect2 = app.feedback_label.get_global_rect()
	var next_rect: Rect2 = app.next_button.get_global_rect()
	_check(feedback.end.y <= next_rect.position.y + TOLERANCE, "Next is below feedback")
	_check(next_rect.position.y - feedback.end.y <= 42, "Next stays immediately below feedback")
	if is_instance_valid(app.explanation_label):
		_check(next_rect.end.y <= app.explanation_label.get_global_rect().position.y + TOLERANCE, "Explanation follows Next")


func _check_result() -> void:
	var controls: Array[Control] = []
	_controls(app, controls)
	var buttons: Array[Button] = []
	for control in controls:
		if control is Button:
			buttons.append(control)
	_check(buttons.size() == 1 and buttons[0].text == "タイトルへ もどる", "Results offer only the approved title return")
	_check(not _visible_text(app).contains("%"), "No percentage on result screens")
	_check_screen()


func _quiz(subject: String, count: int) -> void:
	app.start_quiz(count)
	await _frames()
	var targets: Dictionary = {}
	for index in range(count):
		context = "%s quiz%d question%d" % [subject, count, index + 1]
		_check(app.screen_name == "quiz", "Quiz screen is active")
		var question: Dictionary = app.quiz_session.current_question()
		var item: Dictionary = question["answer"]
		_check(not targets.has(item["key"]), "Correct target does not repeat within a quiz")
		targets[item["key"]] = true
		var choice_keys: Dictionary = {}
		for choice in question["choices"]:
			choice_keys[choice["key"]] = true
		_check(choice_keys.size() == 3 and choice_keys.has(item["key"]), "Three unique choices contain the answer")
		_check(app.choice_buttons.size() == 3, "Exactly three choice buttons are displayed")
		for choice_index in range(app.choice_buttons.size()):
			_check(app.choice_buttons[choice_index].text == question["choices"][choice_index]["name"], "Visible choice names match the state being judged")
		_check(app.question_image.texture.resource_path == app.catalog.quiz_image_path(item["key"]), "Approved silhouette/specimen before answering")
		_check(app.hint_label.text == item["quiz_hint"], "Approved shape hint appears initially")
		if subject == "kinoko":
			_check(app.toxicity_hint_label.text == app.catalog.toxicity_text(item), "Mushroom toxicity hint appears initially")
		else:
			_check(not is_instance_valid(app.toxicity_hint_label) or not app.toxicity_hint_label.visible, "No unrelated toxicity hint for other subjects")
		_check(not app.next_button.visible, "No Next before answer")
		app.next_question(index)
		_check(app.quiz_session.current_index == index, "Cannot skip an unanswered quiz question")
		if index > 0:
			app.select_answer(item["key"], index - 1)
			_check(not app.quiz_session.is_answered(), "Previous question's queued answer is rejected")
		var sound_before: int = app.correct_sound_count
		# Exercise both incorrect feedback and correct feedback in every subject.
		var expected_correct := index != 0
		app.select_answer(item["key"] if expected_correct else _wrong_quiz_key(question), index)
		app.select_answer(item["key"], index)
		await _frames()
		_check(app.correct_sound_count == sound_before + int(expected_correct), "Only the first correct answer plays one sound; wrong/repeated answers are silent")
		_check(app.feedback_label.text == ("せいかい！" if expected_correct else "せいかいは %s" % item["name"]), "Complete correct or incorrect feedback")
		_check(app.question_image.texture.resource_path == app.catalog.color_image_path(item["key"]), "Approved colour/reconstruction image replaces the problem image")
		_check(app.explanation_label.text.contains(item["name"]), "Explanation contains the full subject name")
		if subject != "kinoko":
			_check(app.explanation_label.text.contains(item["zukan_text"]), "Approved explanation text appears after answer")
		for button in app.choice_buttons:
			_check(button.disabled, "All three choices lock after answering")
		_check_answer_layout()
		_check_screen()
		app.next_question(index)
		app.next_question(index)
		await _frames()
	context = "%s quiz%d result" % [subject, count]
	_check(app.screen_name == "result", "Quiz reaches a result screen")
	_check(app.quiz_session.correct_count == count - 1, "Score counts correct answers once")
	_check(app.result_label.text.contains(str(count)) and app.result_label.text.contains(str(count - 1)), "Result contains question and correct counts")
	_check_result()


func _catalogue(subject: String) -> void:
	var pages := ceili(float(SUBJECTS[subject]) / 3.0)
	_check(app.zukan_page_count() == pages, "Encyclopedia page count is calculated from the actual species count")
	for page in range(pages):
		app.show_zukan(page)
		await _frames()
		context = "%s encyclopedia page%d" % [subject, page + 1]
		var expected_cards := mini(3, int(SUBJECTS[subject]) - page * 3)
		_check(app.zukan_cards.size() == expected_cards, "Last page has only the remaining species")
		_check(app.zukan_prev_button.disabled == (page == 0), "Previous respects the first page")
		_check(app.zukan_next_button.disabled == (page == pages - 1), "Next respects the last page")
		_check_screen()
		for offset in range(expected_cards):
			var item: Dictionary = app.catalog.items[page * 3 + offset]
			app.zukan_cards[offset].pressed.emit()
			await _frames()
			context = "%s detail %s" % [subject, item["key"]]
			_check(app.screen_name == "zukan_detail" and app.detail_key == item["key"], "Each image/name card opens the correct detail")
			_check(app.question_image.texture.resource_path == app.catalog.color_image_path(item["key"]), "Detail uses its approved image")
			if subject == "kinoko":
				for field in ["habitat", "season", "size", "color", "features", "quiz_hint", "caution", "similar_kinoko", "trivia"]:
					_check(app.explanation_label.text.contains(item[field]), "Mushroom detail retains %s" % field)
			else:
				_check(app.explanation_label.text.contains(item["zukan_text"]), "Detail retains the approved explanation")
			_check_screen()
			detail_count += 1
			app.show_zukan(app.zukan_page)
			await _frames()
			_check(app.zukan_page == page, "Detail return preserves the original encyclopedia page")


func _arithmetic(subject: String, operation: String) -> void:
	app.start_arithmetic(operation)
	await _frames()
	for index in range(10):
		context = "%s %s question%d" % [subject, operation, index + 1]
		_check(app.screen_name == "arithmetic", "Arithmetic screen is active")
		var question: Dictionary = app.math_session.current_question()
		var left_icons: Array = question["left_icons"]
		var right_icons: Array = question["right_icons"]
		_check(left_icons.size() == question["left"] and right_icons.size() == question["right"], "Illustration counts equal both operands")
		if operation == "subtraction":
			var available := left_icons.duplicate()
			for key in right_icons:
				_check(available.has(key), "Subtraction's removed objects are also shown on the left")
				available.erase(key)
		var icons_expected := index < 4 or index >= 7
		_check(app.arithmetic_icons.size() == (left_icons.size() + right_icons.size() if icons_expected else 0), "1–4 and8–10 show illustration icons;5–7 have no icons")
		var expected_paths: Array[String] = []
		for key in left_icons + right_icons:
			expected_paths.append(app.catalog.color_image_path(key))
		for icon_index in range(app.arithmetic_icons.size()):
			var icon: TextureRect = app.arithmetic_icons[icon_index]
			_check(icon.texture != null and icon.texture.resource_path == expected_paths[icon_index], "Small icons are approved subject images, not emoji")
		var distinct: Dictionary = {}
		for key in left_icons + right_icons:
			distinct[key] = true
		if question["left"] + question["right"] > 1 and operation == "addition":
			_check(distinct.size() > 1, "The same addition question mixes species")
		if question["left"] > 1 and operation == "subtraction":
			_check(distinct.size() > 1, "The subtraction minuend mixes species when possible")
		_check(app.choice_buttons.size() == 3, "Arithmetic has three answer choices")
		for choice_index in range(app.choice_buttons.size()):
			_check(app.choice_buttons[choice_index].text == app.math_session.display_number(question["choices"][choice_index]), "Visible numeric choices match the values being judged")
		_check(not app.next_button.visible, "Arithmetic Next is hidden until answered")
		if index >= 7:
			_check(kanji.search(app.equation_label.text) != null, "Last three equations use kanji numerals")
			for button in app.choice_buttons:
				_check(kanji.search(button.text) != null or button.text == "〇", "Last three answer choices use kanji numerals")
		else:
			_check(kanji.search(app.equation_label.text) == null, "First seven equations use Arabic numerals")
		_check_screen(index >= 7)
		app.next_arithmetic_question(index)
		_check(app.math_session.current_index == index, "Cannot skip an unanswered arithmetic question")
		if index > 0:
			app.select_arithmetic_answer(question["answer"], index - 1)
			_check(not app.math_session.is_answered(), "Previous arithmetic answer cannot answer the next question")
		var sound_before: int = app.correct_sound_count
		var expected_correct := index != 0
		var selected: int = question["answer"]
		if not expected_correct:
			for choice in question["choices"]:
				if choice != question["answer"]:
					selected = choice
					break
		app.select_arithmetic_answer(selected, index)
		app.select_arithmetic_answer(question["answer"], index)
		await _frames()
		_check(app.correct_sound_count == sound_before + int(expected_correct), "Arithmetic has correct-only sound and no repeat playback")
		_check_answer_layout()
		_check_screen(index >= 7)
		app.next_arithmetic_question(index)
		app.next_arithmetic_question(index)
		await _frames()
	context = "%s %s result" % [subject, operation]
	_check(app.screen_name == "result" and app.math_session.correct_count == 9, "Ten arithmetic questions finish with the correct score")
	_check(app.result_label.text.contains("10") and app.result_label.text.contains("9"), "Arithmetic result displays total and correct counts")
	_check_result()


func _placement(question: Dictionary, key: String) -> Dictionary:
	for placement in question["placements"]:
		if placement["key"] == key:
			return placement
	return {}


func _click_search_board(local_position: Vector2) -> void:
	var event := InputEventMouseButton.new()
	event.button_index = MOUSE_BUTTON_LEFT
	event.pressed = true
	event.position = local_position
	app.search_board._gui_input(event)


func _search(subject: String, mode: String) -> void:
	app.start_search(mode)
	await _frames()
	var targets: Dictionary = {}
	for index in range(5):
		context = "%s search/%s question%d" % [subject, mode, index + 1]
		_check(app.screen_name == "search", "Search screen is active")
		var question: Dictionary = app.search_session.current_question()
		var target: Dictionary = question["target"]
		_check(not targets.has(target["key"]), "All five search targets are different")
		targets[target["key"]] = true
		_check(_visible_text(app).contains(target["name"]), "The search task names the target")
		_check(question["items"].size() == 3 and question["placements"].size() == 3, "One correct object plus two other species")
		var image_keys: Dictionary = {}
		for item in question["items"]:
			image_keys[item["key"]] = true
		_check(image_keys.size() == 3 and image_keys.has(target["key"]), "All hidden species are different and include the target")
		var content: Rect2 = app.search_board.content_rect()
		_check(content.size.x > 0 and content.size.y > 0, "Search board has an aspect-contained drawable area")
		var stored_sprites: Dictionary = app.search_board.get("_sprites")
		for item in question["items"]:
			_check(stored_sprites.has(item["key"]) and stored_sprites[item["key"]].resource_path == app.catalog.search_image_path(item["key"], mode), "Search draws the approved native-RGBA resource for the current mode")
		var target_placement := _placement(question, target["key"])
		var target_rect: Rect2 = target_placement["rect"]
		var correct_point := target_rect.get_center()
		var local: Vector2 = app.search_board.normalized_to_local(correct_point)
		_check(app.search_board.local_to_normalized(local).distance_to(correct_point) < 0.0001, "Click conversion stays accurate despite letterboxing and resizing")
		for placement in question["placements"]:
			var sprite: Rect2 = placement["rect"]
			var hit: Rect2 = placement["hit_rect"]
			_check(Rect2(0, 0, 1, 1).encloses(sprite), "Every complete sprite stays in the picture")
			_check(hit.encloses(sprite), "Hit area is at least as large as the visible sprite")
			_check(hit.size.x >= sprite.size.x * 1.5 and hit.size.y >= sprite.size.y * 1.5, "Generous search hit area remains easy to press")
		_check(not app.next_button.visible, "Search Next is hidden until the named target is found")
		app.next_search_question(index)
		_check(app.search_session.current_index == index, "Cannot skip an unfound target")
		if index > 0:
			app.select_search_position(correct_point, index - 1)
			_check(not app.search_session.is_answered(), "Old search clicks cannot answer the next question")
		var wrong_placement: Dictionary = {}
		for placement in question["placements"]:
			if placement["key"] != target["key"]:
				wrong_placement = placement
				break
		var wrong_rect: Rect2 = wrong_placement["rect"]
		var sound_before: int = app.correct_sound_count
		_click_search_board(Vector2(-1, -1))
		_check(app.correct_sound_count == sound_before and not app.search_session.is_answered(), "Clicks outside the drawn background are ignored")
		_click_search_board(app.search_board.normalized_to_local(wrong_rect.get_center()))
		_check(app.correct_sound_count == sound_before and not app.search_session.is_answered(), "Wrong search click is silent and permits retry")
		_click_search_board(local)
		_click_search_board(local)
		await _frames()
		_check(app.search_session.is_answered() and app.search_session.found_count == index + 1, "Correct search click counts once")
		_check(app.search_board.get("_revealed") == true, "Correct search click reveals its identifying circle")
		_check(app.correct_sound_count == sound_before + 1, "Search correct sound plays once")
		_check(app.feedback_label.text == "せいかい！", "Search presents clear correct feedback")
		_check(app.next_button.visible and not app.next_button.disabled, "Found target requires manual Next")
		_check_screen()
		app.next_search_question(index)
		app.next_search_question(index)
		await _frames()
	context = "%s search/%s result" % [subject, mode]
	_check(app.screen_name == "result" and app.search_session.found_count == 5, "Exactly five found targets lead to results")
	_check(app.result_label.text.contains("5"), "Search result displays the five-question count")
	_check_result()


func _stale_sessions(subject: String) -> void:
	context = "%s obsolete session guards" % subject
	app.start_quiz(5)
	var old_generation: int = app.get("_quiz_generation")
	var old_question: Dictionary = app.quiz_session.current_question()
	app.start_quiz(5)
	app.select_answer(old_question["answer"]["key"], 0, old_generation)
	_check(not app.quiz_session.is_answered(), "An old quiz callback cannot answer a restarted game")
	app.start_arithmetic("addition")
	old_generation = app.get("_quiz_generation")
	old_question = app.math_session.current_question()
	app.start_arithmetic("addition")
	app.select_arithmetic_answer(old_question["answer"], 0, old_generation)
	_check(not app.math_session.is_answered(), "An old arithmetic callback cannot answer a restarted game")
	app.start_search("fossil" if subject == "kyouryuu" else "normal")
	old_generation = app.get("_quiz_generation")
	old_question = app.search_session.current_question()
	var previous_target := _placement(old_question, old_question["target"]["key"])
	var previous_rect: Rect2 = previous_target["rect"]
	app.start_search("fossil" if subject == "kyouryuu" else "normal")
	app.select_search_position(previous_rect.get_center(), 0, old_generation)
	_check(not app.search_session.is_answered(), "An old picture click cannot answer a restarted search")
	app.show_title()
	await _frames()
	_check(app.screen_name == "title", "Every game can return to the subject menu")


func _force_large_arithmetic(operation: String, stage: int) -> void:
	var left_count := 4 if operation == "addition" else 9
	var right_count := 5 if operation == "addition" else 9
	var left_icons: Array[String] = []
	var right_icons: Array[String] = []
	for index in range(left_count):
		left_icons.append(app.catalog.items[index]["key"])
	for index in range(right_count):
		right_icons.append(left_icons[index] if operation == "subtraction" else app.catalog.items[left_count + index]["key"])
	app.math_session.questions[stage] = {
		"left": left_count, "right": right_count,
		"answer": 9 if operation == "addition" else 0,
		"choices": [7, 9, 8] if operation == "addition" else [1, 0, 2],
		"left_icons": left_icons, "right_icons": right_icons,
	}
	app.math_session.current_index = stage
	app.math_session.current_result = {}
	app._show_arithmetic_question()


func _responsive(subject: String) -> void:
	for dimensions in CANVASES:
		viewport.size = dimensions
		await _frames()
		context = "%s %dx%d menu" % [subject, dimensions.x, dimensions.y]
		app.show_title()
		await _frames()
		_check_screen()
		app.show_quiz_select()
		await _frames()
		_check_screen()
		app.start_quiz(5)
		await _frames()
		context = "%s %dx%d quiz" % [subject, dimensions.x, dimensions.y]
		_check_screen()
		var question: Dictionary = app.quiz_session.current_question()
		app.select_answer(_wrong_quiz_key(question))
		await _frames()
		_check_answer_layout()
		_check_screen()
		for operation in ["addition", "subtraction"]:
			app.start_arithmetic(operation)
			for stage in [0, 4, 7]:
				# Both the numeral-only prompt and late-stage icon grid must fit;
				# CenterContainer + Japanese text previously collapsed to 1px.
				_force_large_arithmetic(operation, stage)
				await _frames()
				context = "%s %dx%d %s stage%d" % [subject, dimensions.x, dimensions.y, operation, stage + 1]
				_check_screen(stage >= 7)
				app.select_arithmetic_answer(app.math_session.current_question()["answer"])
				await _frames()
				_check_answer_layout()
				_check_screen(stage >= 7)
		app.start_search("reconstruction" if subject == "kyouryuu" else "normal")
		await _frames()
		context = "%s %dx%d search" % [subject, dimensions.x, dimensions.y]
		_check_screen()
		var search_question: Dictionary = app.search_session.current_question()
		var target_placement := _placement(search_question, search_question["target"]["key"])
		var target_rect: Rect2 = target_placement["rect"]
		var point := target_rect.get_center()
		_check(app.search_board.local_to_normalized(app.search_board.normalized_to_local(point)).distance_to(point) < 0.0001, "Resized search hit conversion remains exact")
		_click_search_board(app.search_board.normalized_to_local(point))
		await _frames()
		_check(app.search_session.is_answered(), "The actual board input still selects the target after resizing")
		_check_screen()
		app.show_zukan(app.zukan_page_count() - 1)
		await _frames()
		context = "%s %dx%d last encyclopedia page" % [subject, dimensions.x, dimensions.y]
		_check_screen()
		var item: Dictionary = app.catalog.items.back()
		app.show_zukan_detail(item["key"])
		await _frames()
		_check_screen()
	viewport.size = CANVASES[0]
	await _frames()


func _run() -> void:
	kanji.compile("[\\x{3400}-\\x{4DBF}\\x{4E00}-\\x{9FFF}\\x{F900}-\\x{FAFF}]")
	viewport = SubViewport.new()
	viewport.name = "FullGameViewport"
	viewport.size = CANVASES[0]
	viewport.gui_disable_input = true
	root.add_child(viewport)
	app = MainScene.instantiate()
	viewport.add_child(app)
	await _frames()
	sound_id = app.sound_player.get_instance_id()
	_check(app.screen_name == "subjects", "Startup offers four subject choices")
	if app.screen_name == "error":
		printerr("FAIL: catalogue could not load; synchronize/import assets before running UI integration checks.")
		quit(1)
		return
	_check(app.sound_player.stream.resource_path.ends_with("correct_pingpong.wav"), "Only approved correct sound is loaded")
	_check_screen()
	for subject in SUBJECTS:
		app.select_subject(subject)
		await _frames()
		context = "%s menu" % subject
		_check(app.screen_name == "title", "Subject choice opens its own menu")
		_check(app.catalog.items.size() == SUBJECTS[subject], "Every approved species is loaded")
		_check_screen()
		await _quiz(subject, 5)
		await _quiz(subject, 10)
		await _arithmetic(subject, "addition")
		await _arithmetic(subject, "subtraction")
		if subject == "kyouryuu":
			await _search(subject, "fossil")
			await _search(subject, "reconstruction")
		else:
			await _search(subject, "normal")
		await _catalogue(subject)
		await _stale_sessions(subject)
		await _responsive(subject)
		app.show_subject_select()
		await _frames()
		_check(app.screen_name == "subjects", "Subject menu returns to the four-subject selector")
	_check(detail_count == 117, "All117 encyclopedia details were visited")
	app.sound_player.stop()
	app.sound_player.stream = null
	await create_timer(0.1).timeout
	viewport.queue_free()
	await _frames()
	if failures.is_empty():
		print("PASS: four subjects,117 details,5/10 quizzes,addition/subtraction,all search modes and four PC sizes (%d checks)." % checks)
		quit(0)
	else:
		printerr("FAIL: %d of %d full-game UI/layout checks." % [failures.size(), checks])
		for failure in failures:
			printerr("CHECK FAILURE: %s" % failure)
		quit(1)
