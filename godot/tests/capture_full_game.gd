extends SceneTree
## Optional visual QA: run with a real rendering driver (not --headless).
## Images go only to the explicitly named temporary review directory.

const MainScene = preload("res://scenes/Main.tscn")
const OUTPUT_DIR := "/private/tmp/kinoko-godot-full-game-review"

var app: Control
var viewport: SubViewport
var captures := 0


func _initialize() -> void:
	call_deferred("_run")


func _capture(label: String) -> bool:
	await process_frame
	await process_frame
	await RenderingServer.frame_post_draw
	var image := viewport.get_texture().get_image()
	if image == null or image.is_empty():
		printerr("No rendered pixels available. This optional capture needs a real rendering driver.")
		return false
	var path := "%s/%02d-%s.png" % [OUTPUT_DIR, captures + 1, label]
	if image.save_png(path) != OK:
		printerr("Could not save review image: %s" % path)
		return false
	captures += 1
	print("Captured: %s" % path)
	return true


func _run() -> void:
	if DirAccess.make_dir_recursive_absolute(OUTPUT_DIR) != OK:
		printerr("Could not create the temporary review directory.")
		quit(1)
		return
	root.size = Vector2i(1280, 800)
	viewport = SubViewport.new()
	viewport.size = Vector2i(1280, 800)
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	app = MainScene.instantiate()
	viewport.add_child(app)
	await process_frame
	if app.screen_name == "error":
		printerr("Synchronize/import approved assets before capturing review images.")
		quit(1)
		return
	if not await _capture("subjects"):
		quit(1)
		return
	app.select_subject("kinoko")
	await _capture("mushroom-menu")
	app.start_quiz(5)
	await _capture("mushroom-quiz-before")
	app.select_answer(app.quiz_session.current_question()["answer"]["key"])
	await _capture("mushroom-quiz-after")
	app.select_subject("shokubutsu")
	app.start_quiz(5)
	await _capture("plant-quiz-before")
	app.select_subject("konchuu")
	app.start_arithmetic("subtraction")
	app.math_session.current_index = 7
	app._show_arithmetic_question()
	await _capture("insect-subtraction-kanji")
	app.select_subject("kyouryuu")
	app.start_search("fossil")
	await _capture("fossil-search")
	app.start_search("reconstruction")
	await _capture("dinosaur-search")
	app.start_quiz(5)
	app.select_answer(app.quiz_session.current_question()["answer"]["key"])
	await _capture("dinosaur-quiz-after")
	app.show_zukan(app.zukan_page_count() - 1)
	await _capture("dinosaur-encyclopedia")
	app.sound_player.stop()
	app.sound_player.stream = null
	await create_timer(0.1).timeout
	viewport.queue_free()
	await process_frame
	print("Saved%d rendered review images to %s" % [captures, OUTPUT_DIR])
	quit(0)
