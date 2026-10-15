extends "res://tests/test_full_game_ui.gd"
## Exhaust every approved name and hint instead of relying on random sampling.
## Shared geometry helpers are inherited from the real-scene integration suite.


func _force_question(item_index: int) -> Dictionary:
	var item: Dictionary = app.catalog.items[item_index]
	var choices: Array[Dictionary] = [item,
		app.catalog.items[(item_index + 1) % app.catalog.items.size()],
		app.catalog.items[(item_index + 2) % app.catalog.items.size()]]
	var questions: Array[Dictionary] = [{"answer": item, "choices": choices}]
	app.quiz_session.questions = questions
	app.quiz_session.current_index = 0
	app.quiz_session.correct_count = 0
	app.quiz_session.current_result = {}
	app._show_question()
	return questions[0]


func _run() -> void:
	kanji.compile("[\\x{3400}-\\x{4DBF}\\x{4E00}-\\x{9FFF}\\x{F900}-\\x{FAFF}]")
	viewport = SubViewport.new()
	viewport.name = "FullCatalogueLayoutViewport"
	viewport.size = CANVASES[0]
	viewport.gui_disable_input = true
	root.add_child(viewport)
	app = MainScene.instantiate()
	viewport.add_child(app)
	await _frames()
	sound_id = app.sound_player.get_instance_id()
	_check(app.screen_name == "subjects", "The full catalogue loads at startup")
	if app.screen_name == "error":
		printerr("FAIL: synchronize/import approved assets before running exhaustive layout checks.")
		quit(1)
		return
	var records_checked := 0
	for dimensions in CANVASES:
		viewport.size = dimensions
		await _frames()
		for subject in SUBJECTS:
			app.select_subject(subject)
			app.start_quiz(5)
			for item_index in range(app.catalog.items.size()):
				var question := _force_question(item_index)
				var item: Dictionary = question["answer"]
				context = "%s %s %dx%d before" % [subject, item["key"], dimensions.x, dimensions.y]
				await _frames()
				_check(app.choice_buttons.size() == 3, "Exactly three choices")
				_check(app.choice_buttons[0].text == item["name"], "Correct species is visibly selectable")
				_check(app.question_image.texture.resource_path == app.catalog.quiz_image_path(item["key"]), "Correct silhouette/specimen before answering")
				_check(app.hint_label.text == item["quiz_hint"], "Every approved hint remains complete")
				_check(app.hint_label.get_theme_font_size("font_size") == 32, "Every shape hint retains the approved large font")
				_check(app.next_button.get_theme_font_size("font_size") == 32, "Next retains the approved large font")
				for button in app.choice_buttons:
					_check(button.get_theme_font_size("font_size") == 32, "Every choice uses the same large font as Next")
				if subject == "kinoko":
					_check(app.toxicity_hint_label.get_theme_font_size("font_size") == 32, "Every mushroom toxicity hint retains the large font")
					_check(app.toxicity_hint_label.text == app.catalog.toxicity_text(item), "Complete approved toxicity hint")
				_check_screen()
				var sound_before: int = app.correct_sound_count
				app.select_answer(question["choices"][1]["key"])
				await _frames()
				context = "%s %s %dx%d after" % [subject, item["key"], dimensions.x, dimensions.y]
				_check(app.feedback_label.text == "せいかいは %s" % item["name"], "The longest incorrect feedback keeps the entire correct name")
				_check(app.correct_sound_count == sound_before, "All incorrect answers remain silent")
				_check(app.question_image.texture.resource_path == app.catalog.color_image_path(item["key"]), "The approved colour/reconstruction image appears after answering")
				_check_answer_layout()
				_check_screen()
				records_checked += 1
	_check(records_checked == 117 * CANVASES.size(), "All117 names and hints were checked at all four PC sizes")
	app.sound_player.stop()
	app.sound_player.stream = null
	await create_timer(0.1).timeout
	viewport.queue_free()
	await _frames()
	if failures.is_empty():
		print("PASS: all117 species before/after quiz feedback at four PC sizes (%d checks)." % checks)
		quit(0)
	else:
		printerr("FAIL: %d of %d exhaustive catalogue layout checks." % [failures.size(), checks])
		for failure in failures:
			printerr("CHECK FAILURE: %s" % failure)
		quit(1)
