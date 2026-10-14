extends SceneTree
## Run the real scene headlessly; all gameplay buttons remain in the PC canvas.

const MainScene = preload("res://scenes/Main.tscn")
var checks := 0
var failures: Array[String] = []
var app: Control
var kanji := RegEx.new()


func _initialize() -> void:
	call_deferred("_run")


func _check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		push_error(message)


func _frames() -> void:
	await process_frame
	await process_frame


func _visible_text(node: Node) -> String:
	var result := ""
	if node is Control and not node.is_visible_in_tree():
		return result
	if node is Label or node is Button:
		result += node.text + "\n"
	for child in node.get_children():
		result += _visible_text(child)
	return result


func _check_controls(node: Node) -> void:
	if node is Control and not node.is_visible_in_tree():
		return
	if node is Button:
		var rect: Rect2 = node.get_global_rect()
		_check(rect.position.x >= -1 and rect.position.y >= -1
			and rect.end.x <= 1281 and rect.end.y <= 801,
			"Button outside PC canvas: %s %s" % [node.text, rect])
		_check(node.get_theme_color("font_color") == Color.BLACK, "Button text must be black")
	if node is Label:
		_check(node.get_theme_color("font_color") == Color.BLACK, "Label text must be black")
	for child in node.get_children():
		_check_controls(child)


func _check_screen() -> void:
	var text := _visible_text(app)
	_check(kanji.search(text) == null, "Game screen must not contain kanji: %s" % text)
	_check_controls(app)


func _run() -> void:
	root.size = Vector2i(1280, 800)
	kanji.compile("[\\x{3400}-\\x{4DBF}\\x{4E00}-\\x{9FFF}\\x{F900}-\\x{FAFF}]")
	app = MainScene.instantiate()
	root.add_child(app)
	await _frames()
	_check(app.screen_name == "title", "Main scene should show mushroom title")
	_check(app.catalog.items.size() == 30, "Catalogue should contain 30 mushrooms")
	_check(app.zukan_page_count() == 10, "Encyclopedia should contain 10 pages")
	_check(not _visible_text(app).contains("しょくぶつ"), "Prototype should be mushroom-only")
	_check_screen()
	var sound_id: int = app.sound_player.get_instance_id()
	_check(app.sound_player.stream.resource_path.ends_with("correct_pingpong.wav"), "Correct sound source")

	app.show_quiz_select()
	await _frames()
	_check(app.screen_name == "quiz_select", "Question count screen")
	_check_screen()
	for count in [5, 10]:
		app.start_quiz(count)
		await _frames()
		for index in range(count):
			_check(app.screen_name == "quiz", "Question screen is shown")
			var question: Dictionary = app.quiz_session.current_question()
			var item: Dictionary = question["answer"]
			_check(app.choice_buttons.size() == 3, "Exactly three choice buttons")
			_check(app.question_image.texture.resource_path == app.catalog.quiz_image_path(item["key"]), "Silhouette before answer")
			_check(app.hint_label.text == item["quiz_hint"], "Approved form hint present initially")
			_check(app.toxicity_hint_label.text == app.catalog.toxicity_text(item), "Toxicity hint present initially")
			_check(not app.next_button.visible, "Next hidden before answer")
			app.next_question()
			_check(app.quiz_session.current_index == index, "Next cannot skip unanswered question")
			if index > 0:
				app.select_answer(item["key"], index - 1)
				_check(not app.quiz_session.is_answered(), "Stale queued answer is rejected")
			var old_sound_count: int = app.correct_sound_count
			app.select_answer(item["key"])
			_check(app.correct_sound_count == old_sound_count + 1, "Correct answer triggers sound exactly once")
			app.select_answer(item["key"])
			_check(app.correct_sound_count == old_sound_count + 1, "Repeated answer does not replay sound")
			_check(app.quiz_session.correct_count == index + 1, "Repeated answer does not increase score")
			await _frames()
			_check(app.question_image.texture.resource_path == app.catalog.color_image_path(item["key"]), "Colour image after answer")
			_check(app.feedback_label.text == "せいかい！", "Correct feedback")
			for field in ["name", "habitat", "features", "caution"]:
				_check(app.explanation_label.text.contains(item[field]), "Approved answer explanation: %s" % field)
			_check(app.next_button.visible and not app.next_button.disabled, "Next appears after answer")
			_check(app.next_button.global_position.y < app.explanation_label.global_position.y, "Next immediately below feedback, before explanation")
			for button in app.choice_buttons:
				_check(button.disabled, "All choices locked after answer")
			_check(app.sound_player.get_instance_id() == sound_id, "Sound survives screen changes")
			_check_screen()
			app.next_question(index)
			app.next_question(index)
			await _frames()
		_check(app.screen_name == "result", "Result screen after last question")
		_check(app.result_label.text.contains(str(count)), "Result contains total question count")
		_check(not _visible_text(app).contains("%"), "Result has no rate")
		_check(_visible_text(app).replace("\n", " ").contains("これで きみも きのこ はかせだ！！"), "Full score message")
		_check_screen()
		app.show_title()
		await _frames()

	app.start_quiz(5)
	await _frames()
	var wrong_question: Dictionary = app.quiz_session.current_question()
	var wrong_key := ""
	for choice in wrong_question["choices"]:
		if choice["key"] != wrong_question["answer"]["key"]:
			wrong_key = choice["key"]
			break
	var old_sound_count: int = app.correct_sound_count
	app.select_answer(wrong_key)
	await _frames()
	_check(app.correct_sound_count == old_sound_count, "Wrong answer is silent")
	_check(app.feedback_label.text == "せいかいは %s" % wrong_question["answer"]["name"], "Wrong answer shows correct name")
	_check(app.quiz_session.correct_count == 0, "Wrong answer does not increase score")
	_check_screen()
	app.show_title()
	await _frames()
	_check(app.screen_name == "title", "Quit quiz to title")

	for page in range(10):
		app.show_zukan(page)
		await _frames()
		_check(app.zukan_page == page, "Requested encyclopedia page")
		_check(app.zukan_cards.size() == 3, "Three cards on every page")
		_check(app.zukan_prev_button.disabled == (page == 0), "Previous boundary")
		_check(app.zukan_next_button.disabled == (page == 9), "Next boundary")
		_check_screen()
		for offset in range(3):
			var item: Dictionary = app.catalog.items[page * 3 + offset]
			app.zukan_cards[offset].pressed.emit()
			await _frames()
			_check(app.screen_name == "zukan_detail", "Image/name card opens detail")
			_check(app.detail_key == item["key"], "Detail for selected mushroom")
			for field in ["habitat", "season", "size", "color", "features", "quiz_hint", "caution", "similar_kinoko", "trivia"]:
				_check(app.explanation_label.text.contains(item[field]), "Approved detail field: %s" % field)
			if item["cooking"] != null:
				_check(app.explanation_label.text.contains(item["cooking"]), "Edible mushroom cooking details")
			_check_screen()
			app.show_zukan(app.zukan_page)
			await _frames()
			_check(app.zukan_page == page, "Back restores encyclopedia page")

	app.show_title()
	await _frames()
	_check(app.sound_player.get_instance_id() == sound_id, "One persistent sound node")
	app.queue_free()
	await _frames()
	if failures.is_empty():
		print("PASS: mushroom UI, 5/10 quiz, all 30 encyclopedia details, sound and layout (%d checks)." % checks)
		quit(0)
	else:
		printerr("FAIL: %d of %d mushroom UI checks." % [failures.size(), checks])
		quit(1)
