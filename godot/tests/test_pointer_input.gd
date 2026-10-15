extends SceneTree
## Exercise the engine's GUI event routing, not direct button signals or handlers.
## This protects card child controls and resized/letterboxed search hit areas.

const MainScene = preload("res://scenes/Main.tscn")
const SUBJECTS := ["kinoko", "shokubutsu", "konchuu", "kyouryuu"]
const CANVASES := [Vector2i(1280, 800), Vector2i(1366, 768), Vector2i(1600, 900), Vector2i(1920, 1080)]

var viewport: SubViewport
var app: Control
var checks := 0
var failures: Array[String] = []


func _initialize() -> void:
	call_deferred("_run")


func _frames() -> void:
	await process_frame
	await process_frame
	await process_frame


func _check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		push_error(message)


func _find_type(node: Node, type_name: String) -> Node:
	for child in node.get_children():
		if child.is_class(type_name):
			return child
		var found := _find_type(child, type_name)
		if found != null:
			return found
	return null


func _buttons(node: Node) -> Array[Button]:
	var result: Array[Button] = []
	for child in node.get_children():
		if child is Button:
			result.append(child)
		result.append_array(_buttons(child))
	return result


func _click(point: Vector2) -> void:
	var motion := InputEventMouseMotion.new()
	motion.position = point
	motion.global_position = point
	viewport.push_input(motion, true)
	for pressed in [true, false]:
		var event := InputEventMouseButton.new()
		event.button_index = MOUSE_BUTTON_LEFT
		event.pressed = pressed
		event.button_mask = MOUSE_BUTTON_MASK_LEFT if pressed else 0
		event.position = point
		event.global_position = point
		viewport.push_input(event, true)
	await _frames()


func _run() -> void:
	viewport = SubViewport.new()
	viewport.size = CANVASES[0]
	viewport.gui_disable_input = false
	viewport.handle_input_locally = true
	root.add_child(viewport)
	app = MainScene.instantiate()
	viewport.add_child(app)
	await _frames()
	if app.screen_name == "error":
		_check(false, "Synchronize and import approved assets before running pointer tests")
		await _cleanup()
		return
	for index in range(SUBJECTS.size()):
		for type_name in ["TextureRect", "Label"]:
			app.show_subject_select()
			await _frames()
			var cards := _buttons(app)
			var target := _find_type(cards[index], type_name) as Control
			await _click(target.get_global_rect().get_center())
			_check(app.screen_name == "title" and app.catalog.subject_id == SUBJECTS[index],
				"Subject card %s %s receives real routed click" % [SUBJECTS[index], type_name])
	for subject in SUBJECTS:
		app.select_subject(subject)
		for type_name in ["TextureRect", "Label"]:
			app.show_zukan(1)
			await _frames()
			var expected_key: String = app.catalog.items[3]["key"]
			var target := _find_type(app.zukan_cards[0], type_name) as Control
			await _click(target.get_global_rect().get_center())
			_check(app.screen_name == "zukan_detail" and app.detail_key == expected_key,
				"Encyclopedia %s %s receives real routed click" % [subject, type_name])
		for mode in (["fossil", "reconstruction"] if subject == "kyouryuu" else ["normal"]):
			for dimensions in CANVASES:
				viewport.size = dimensions
				app.start_search(mode)
				await _frames()
				var question: Dictionary = app.search_session.current_question()
				for placement in question["placements"]:
					if placement["key"] != question["target"]["key"]:
						var wrong_rect: Rect2 = placement["rect"]
						await _click(app.search_board.global_position + app.search_board.normalized_to_local(wrong_rect.get_center()))
						_check(not app.search_session.is_answered(),
							"Wrong sprite click remains retryable %s %s %s" % [subject, mode, dimensions])
						break
				for placement in question["placements"]:
					if placement["key"] == question["target"]["key"]:
						var correct_rect: Rect2 = placement["rect"]
						await _click(app.search_board.global_position + app.search_board.normalized_to_local(correct_rect.get_center()))
						_check(app.search_session.is_answered(),
							"Correct search receives real routed click %s %s %s" % [subject, mode, dimensions])
						break
	await _cleanup()


func _cleanup() -> void:
	app.sound_player.stop()
	app.sound_player.stream = null
	await create_timer(0.1).timeout
	viewport.queue_free()
	await _frames()
	app = null
	viewport = null
	# Let the awaiting input/run coroutines release their temporary resources
	# before ending the SceneTree, instead of quitting from their final await.
	call_deferred("_finish")


func _finish() -> void:
	if failures.is_empty():
		print("PASS: actual pointer routing (%d checks, 0 failures)." % checks)
	else:
		printerr("FAIL: actual pointer routing (%d checks, %d failures)." % [checks, failures.size()])
	quit(0 if failures.is_empty() else 1)
