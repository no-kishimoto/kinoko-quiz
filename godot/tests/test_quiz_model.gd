extends SceneTree
## Run with Godot --headless --path godot --script res://tests/test_quiz_model.gd.

const CatalogModel = preload("res://scripts/KinokoCatalog.gd")
const SessionModel = preload("res://scripts/QuizSession.gd")
const TEXT_FIELDS := [
	"name", "habitat", "season", "size", "color", "features", "quiz_hint",
	"caution", "similar_kinoko", "trivia",
]
var _checks := 0
var _failures := 0


func _init() -> void:
	var catalogue := CatalogModel.new()
	if not _check(catalogue.load_data(), "Catalogue load failed: %s" % catalogue.error_message):
		_finish()
		return
	_test_catalogue(catalogue)
	_test_guards(catalogue.items)
	_test_seed_reproducibility(catalogue.items)
	for count in [5, 10]:
		for seed_value in range(50):
			_test_complete_session(catalogue.items, count, seed_value)
	_finish()


func _test_catalogue(catalogue: RefCounted) -> void:
	_check(catalogue.items.size() == 30, "Expected 30 mushroom species")
	var keys: Dictionary = {}
	var names: Dictionary = {}
	var kanji := RegEx.new()
	_check(kanji.compile("[\\x{3400}-\\x{4dbf}\\x{4e00}-\\x{9fff}\\x{f900}-\\x{faff}]") == OK, "Kanji validation regex")
	for item in catalogue.items:
		var key: String = item["key"]
		_check(not keys.has(key), "Duplicate catalogue key: %s" % key)
		_check(not names.has(item["name"]), "Duplicate catalogue name: %s" % key)
		keys[key] = true
		names[item["name"]] = true
		_check(catalogue.get_item(key) == item, "Key lookup: %s" % key)
		for field in TEXT_FIELDS:
			var text: String = item.get(field, "")
			_check(not text.strip_edges().is_empty(), "Missing explanation field %s: %s" % [field, key])
			_check(kanji.search(text) == null, "Kanji in %s: %s" % [field, key])
		if item.get("cooking") is String:
			_check(kanji.search(item["cooking"]) == null, "Kanji in cooking: %s" % key)
		var highlight: Dictionary = item.get("highlight", {})
		_check(not str(highlight.get("part", "")).is_empty(), "Missing feature-circle part: %s" % key)
		_check(float(highlight.get("x", -1)) >= 0.0 and float(highlight.get("x", 2)) <= 1.0, "Feature-circle x: %s" % key)
		_check(float(highlight.get("y", -1)) >= 0.0 and float(highlight.get("y", 2)) <= 1.0, "Feature-circle y: %s" % key)
		_check(float(highlight.get("radius", -1)) > 0.0 and float(highlight.get("radius", 1)) <= 0.5, "Feature-circle radius: %s" % key)
		var quiz_path: String = catalogue.quiz_image_path(key)
		var colour_path: String = catalogue.color_image_path(key)
		_check(quiz_path == "res://assets/images/quiz/%s.png" % key, "Quiz resource path: %s" % key)
		_check(colour_path == "res://assets/images/zukan/%s.png" % key, "Colour resource path: %s" % key)
		if not _check(ResourceLoader.exists(quiz_path) and ResourceLoader.exists(colour_path), "Images missing or not imported: %s" % key):
			continue
		var quiz: Texture2D = load(quiz_path)
		var colour: Texture2D = load(colour_path)
		if not _check(quiz != null and colour != null, "Images must load as textures: %s" % key):
			continue
		_check(quiz.get_size() == colour.get_size(), "Quiz and colour sizes match: %s" % key)
		_check(colour.get_size() == Vector2(1254, 1254), "Original image dimensions: %s" % key)
		var quiz_image := quiz.get_image()
		var colour_image := colour.get_image()
		_check(colour_image.detect_alpha() != Image.ALPHA_NONE, "Colour background must stay transparent: %s" % key)
		_check(quiz_image.detect_alpha() != Image.ALPHA_NONE, "Quiz background must stay transparent: %s" % key)
		# Compare transparent edges and opaque subject pixels without regenerating masks.
		for y in range(0, colour_image.get_height(), 128):
			for x in range(0, colour_image.get_width(), 128):
				_check(is_equal_approx(colour_image.get_pixel(x, y).a, quiz_image.get_pixel(x, y).a), "Quiz keeps original alpha %s at %d,%d" % [key, x, y])
		if key == "sorairotake":
			_test_sorairotake_alpha(colour_image, colour_path)
	_check(keys.size() == 30 and names.size() == 30, "All species names and keys are distinct")
	_check(catalogue.get_item("not_a_mushroom").is_empty(), "Unknown key gives empty lookup")
	_check(catalogue.toxicity_text({"toxicity": "poisonous"}) == "どくあり", "Poisonous label")
	_check(catalogue.toxicity_text({"toxicity": "non_poisonous"}) == "どくなし", "Nonpoisonous label")
	_check(catalogue.toxicity_text({"toxicity": "unknown"}) == "どくが あるか わかっていない", "Unknown toxicity is not guessed")
	_check(ResourceLoader.exists("res://assets/sounds/correct_pingpong.wav"), "Correct sound is prepared")
	_check(not FileAccess.file_exists("res://assets/sounds/incorrect_buzzer.wav"), "Incorrect sound is not prepared")


func _test_sorairotake_alpha(imported_image: Image, path: String) -> void:
	# Source-byte comparison is a developer test; gameplay loads Texture2D resources.
	var original := Image.new()
	if not _check(original.load_png_from_buffer(FileAccess.get_file_as_bytes(path)) == OK, "Sorairotake original PNG loads"):
		return
	var opaque_blue_pixels := 0
	var transparent_pixels := 0
	for y in range(0, original.get_height(), 24):
		for x in range(0, original.get_width(), 24):
			var pixel := original.get_pixel(x, y)
			if pixel.a < 0.01:
				transparent_pixels += 1
			if pixel.a >= 0.98 and pixel.b > pixel.r + 0.15 and pixel.g > pixel.r + 0.15:
				opaque_blue_pixels += 1
				_check(imported_image.get_pixel(x, y).a >= 0.98, "Sorairotake blue subject stays opaque at %d,%d" % [x, y])
	_check(opaque_blue_pixels > 20, "Sorairotake test covers opaque blue cap/body")
	_check(transparent_pixels > 20, "Sorairotake test covers transparent background")


func _test_guards(items: Array[Dictionary]) -> void:
	var session := SessionModel.new(_rng(42))
	_check(session.is_finished(), "Empty session has no playable question")
	_check(session.current_question().is_empty(), "Empty session question")
	_check(session.answer(items[0]["key"]).is_empty(), "No answer before start")
	for count in [-1, 0, 1, 4, 6, 9, 11]:
		_check(not session.start(items, count), "Reject unsupported count %d" % count)
		_check(not session.error_message.is_empty(), "Invalid count has diagnostic")
		_check(session.questions.is_empty(), "Invalid start clears old questions")
	var small: Array[Dictionary] = []
	for index in range(4):
		small.append(items[index])
	_check(not session.start(small, 5), "Reject too few species")
	var duplicate: Array[Dictionary] = items.duplicate()
	duplicate[1] = duplicate[0]
	_check(not session.start(duplicate, 5), "Reject duplicate names/keys")
	_check(session.start(items, 5), "Start valid guarded session")
	_check(not session.next_question(), "Next before answer is not finished")
	_check(session.current_index == 0, "Next before answer does not advance")
	_check(session.answer("not_a_choice").is_empty(), "Reject invalid selection")
	_check(not session.is_answered() and session.correct_count == 0, "Invalid answer does not mutate state")
	var correct_key: String = session.current_question()["answer"]["key"]
	var result: Dictionary = session.answer(correct_key)
	_check(result.get("is_correct", false), "Valid correct answer accepted")
	_check(session.is_answered() and session.correct_count == 1, "Correct score counted once")
	_check(session.answer(correct_key).is_empty(), "Repeated answer rejected")
	_check(session.correct_count == 1, "Repeated answer never rescores")
	_check(not session.next_question() and session.current_index == 1, "Explicit next advances exactly once")
	_check(not session.is_answered() and session.current_result.is_empty(), "Next clears previous answer")
	_check(not session.next_question() and session.current_index == 1, "Repeated next does not skip unanswered question")
	_check(session.start(items, 10), "Restart valid quiz")
	_check(session.current_index == 0 and session.correct_count == 0 and not session.is_answered(), "Restart resets all progress")
	# A model must never own an audio node or request wrong-answer audio.
	_check(session is RefCounted and not session.has_method("play"), "Quiz model cannot play sounds")


func _test_seed_reproducibility(items: Array[Dictionary]) -> void:
	var first := SessionModel.new(_rng(20261014))
	var second := SessionModel.new(_rng(20261014))
	_check(first.start(items, 10) and second.start(items, 10), "Seeded sessions start")
	_check(first.questions == second.questions, "Identical seeds create identical questions and choice ordering")


func _test_complete_session(items: Array[Dictionary], count: int, seed_value: int) -> void:
	var session := SessionModel.new(_rng(seed_value))
	if not _check(session.start(items, count), "Session starts: count %d seed %d" % [count, seed_value]):
		return
	_check(session.total_questions() == count, "Requested question total")
	var seen_answers: Dictionary = {}
	var expected_score := 0
	for index in range(count):
		var question: Dictionary = session.current_question()
		if not _check(not question.is_empty(), "Playable question %d" % index):
			break
		var correct: Dictionary = question["answer"]
		_check(not seen_answers.has(correct["key"]), "Answers do not repeat within session")
		seen_answers[correct["key"]] = true
		_check(session.progress_text() == "もんだい %d / %d" % [index + 1, count], "Progress label")
		var choices: Array[Dictionary] = question["choices"]
		_check(choices.size() == 3, "Exactly three choices")
		var choice_keys: Dictionary = {}
		var correct_occurrences := 0
		var wrong_key := ""
		for choice in choices:
			choice_keys[choice["key"]] = true
			if choice["key"] == correct["key"]:
				correct_occurrences += 1
			else:
				wrong_key = choice["key"]
		_check(choice_keys.size() == 3, "Choice keys are all different")
		_check(correct_occurrences == 1, "Correct answer appears exactly once")
		# Include both all-correct and mixed-result runs without changing choices.
		var should_be_correct := seed_value % 2 == 0 or index % 2 == 0
		var selected: String = correct["key"] if should_be_correct else wrong_key
		var result: Dictionary = session.answer(selected)
		_check(not result.is_empty(), "Answer accepted")
		_check(result.get("is_correct") == should_be_correct, "Correct/wrong outcome")
		_check(result.get("answer") == correct, "Feedback always points to correct species")
		_check(result.get("selected_key") == selected, "Selected key is retained")
		if should_be_correct:
			expected_score += 1
		_check(session.correct_count == expected_score, "Score includes only correct answers")
		_check(session.answer(selected).is_empty(), "Rapid repeated answer rejected")
		_check(session.correct_count == expected_score, "No rapid-click score mutation")
		var finished: bool = session.next_question()
		_check(finished == (index == count - 1), "Finished only after last explicit next")
	_check(seen_answers.size() == count, "All requested questions played")
	_check(session.is_finished(), "Session finishes")
	_check(session.correct_count == expected_score, "Final score is exact")
	_check(session.current_question().is_empty(), "No question after finish")
	_check(session.answer(items[0]["key"]).is_empty(), "No answer after finish")
	var final_index: int = session.current_index
	_check(session.next_question() and session.current_index == final_index, "Next after finish does not advance again")


func _rng(seed_value: int) -> RandomNumberGenerator:
	var randomizer := RandomNumberGenerator.new()
	randomizer.seed = seed_value
	return randomizer


func _check(condition: bool, message: String) -> bool:
	_checks += 1
	if not condition:
		_failures += 1
		push_error("MODEL TEST FAILED: " + message)
	return condition


func _finish() -> void:
	if _failures:
		print("Mushroom Godot model tests: %d failures / %d checks" % [_failures, _checks])
		quit(1)
	else:
		print("Mushroom Godot model tests: %d checks passed; 30 species; 100 seeded 5/10-question sessions" % _checks)
		quit(0)
