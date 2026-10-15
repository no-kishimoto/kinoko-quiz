extends SceneTree
## Pure-state and prepared-asset regression tests for all 117 species.

const CatalogModel = preload("res://scripts/SubjectCatalog.gd")
const ArithmeticModel = preload("res://scripts/ArithmeticSession.gd")
const SearchModel = preload("res://scripts/SearchSession.gd")
const COUNTS := {"kinoko": 30, "shokubutsu": 40, "konchuu": 29, "kyouryuu": 18}

var _checks := 0
var _failures := 0


func _init() -> void:
	_test_guards()
	_test_seed_reproducibility()
	var catalog := CatalogModel.new()
	if _check(catalog.load_data(), "Full catalogue loads: %s" % catalog.error_message):
		_test_catalog(catalog)
		for subject in COUNTS:
			_check(catalog.select_subject(subject), "Subject selection: %s" % subject)
			for seed_value in range(30):
				_test_arithmetic(catalog.items, "addition", seed_value)
				_test_arithmetic(catalog.items, "subtraction", seed_value)
				var config: Dictionary = catalog.subjects[subject]
				if subject == "kyouryuu":
					_test_search(catalog.items, config["fossil_backgrounds"], "fossil", {}, {}, seed_value)
					_test_search(catalog.items, [], "reconstruction", config["habitats"], config["habitat_backgrounds"], seed_value)
				else:
					_test_search(catalog.items, config["backgrounds"], "normal", {}, {}, seed_value)
	print("Full-model tests: %d checks, %d failures" % [_checks, _failures])
	quit(0 if _failures == 0 else 1)


func _test_catalog(catalog: RefCounted) -> void:
	_check(catalog.subjects.size() == 4, "Exactly four subjects")
	var total := 0
	for identifier in COUNTS:
		_check(catalog.select_subject(identifier), "Can select %s" % identifier)
		_check(catalog.subject_id == identifier, "Selected subject ID")
		_check(catalog.items.size() == COUNTS[identifier], "Approved species count: %s" % identifier)
		total += catalog.items.size()
		var seen: Dictionary = {}
		for item in catalog.items:
			var key: String = item["key"]
			_check(not seen.has(key), "Unique species key: %s" % key)
			seen[key] = true
			_check(catalog.get_item(key) == item, "Full record lookup: %s" % key)
			_check(ResourceLoader.exists(catalog.quiz_image_path(key)), "Quiz image imported: %s" % key)
			_check(ResourceLoader.exists(catalog.color_image_path(key)), "Colour image imported: %s" % key)
			_check(ResourceLoader.exists(catalog.search_image_path(key)), "Search image imported: %s" % key)
			if identifier == "kyouryuu":
				_check(catalog.search_image_path(key, "fossil") == item["fossil_image"], "Independent approved fossil mapping: %s" % key)
				_check(catalog.search_image_path(key, "reconstruction") == item["search_image"], "Independent approved reconstruction mapping: %s" % key)
			elif identifier == "kinoko":
				for field in ["habitat", "season", "size", "color", "features", "caution", "similar_kinoko", "trivia", "edibility", "toxicity"]:
					_check(item.has(field), "Rich mushroom field preserved: %s %s" % [key, field])
		_check(catalog.get_item("__missing__").is_empty(), "Unknown species lookup is empty")
	_check(total == 117, "Exactly 117 species")
	var previous: String = catalog.subject_id
	_check(not catalog.select_subject("invalid"), "Unknown subject rejected")
	_check(catalog.subject_id == previous, "Invalid selection does not replace active subject")
	_check(catalog.select_subject("kinoko"), "Valid selection clears selection error")
	_check(catalog.error_message.is_empty(), "No stale catalogue error")
	_check(catalog.toxicity_text({"toxicity": "unknown"}) == "どくが あるか わかっていない", "Toxicity is not guessed")


func _test_arithmetic(items: Array[Dictionary], operation: String, seed_value: int) -> void:
	var session := ArithmeticModel.new(_rng(seed_value))
	if not _check(session.start(items, operation), "Arithmetic start: %s" % session.error_message):
		return
	_check(session.total_questions() == 10, "Arithmetic always ten questions")
	var previous_pairs: Dictionary = {}
	var allowed_keys: Dictionary = {}
	for item in items:
		allowed_keys[item["key"]] = true
	for index in range(10):
		_check(session.current_index == index, "Arithmetic current index")
		_check(session.progress_text() == "もんだい %d / 10" % (index + 1), "Arithmetic progress label")
		_check(session.shows_icons() == (index < 4 or index >= 7), "Approved illustration stages")
		_check(session.uses_kanji_numerals() == (index >= 7), "Approved kanji numeral stages")
		for value in range(10):
			var expected: String = ArithmeticModel.KANJI_NUMERALS[value] if index >= 7 else str(value)
			_check(session.display_number(value) == expected, "Equation and answer numeral formatting")
		var question: Dictionary = session.current_question()
		var left: int = question["left"]
		var right: int = question["right"]
		var correct: int = question["answer"]
		var pair_key := "%d:%d" % [left, right]
		_check(not previous_pairs.has(pair_key), "No repeated arithmetic ordered pair")
		previous_pairs[pair_key] = true
		if operation == "addition":
			_check(left in range(1, 9) and right in range(1, 9), "Addition operands are 1..8")
			_check(left + right == correct and correct <= 9, "Addition has no carrying")
		else:
			_check(left in range(1, 10) and right in range(1, left + 1), "Subtraction operands are one digit")
			_check(left - right == correct and correct >= 0, "Subtraction is nonnegative, including zero")
		var choices: Array = question["choices"]
		_check(choices.size() == 3 and choices.has(correct), "Correct arithmetic answer is always among three choices")
		_check(choices[0] != choices[1] and choices[0] != choices[2] and choices[1] != choices[2], "Arithmetic choices are distinct")
		for value in choices:
			_check(value is int and value >= 0 and value <= 9, "Arithmetic choices are one-digit integers")
		var left_icons: Array = question["left_icons"]
		var right_icons: Array = question["right_icons"]
		_check(left_icons.size() == left and right_icons.size() == right, "Illustration counts equal operands")
		var all_icons: Array = left_icons + right_icons
		for key in all_icons:
			_check(allowed_keys.has(key), "Icons only use active subject species, not emoji")
		_check(left_icons[0] != left_icons[1] if left >= 2 else true, "Species mix within an illustrated operand")
		if operation == "subtraction":
			for icon_index in range(right):
				_check(right_icons[icon_index] == left_icons[icon_index], "Subtraction removes exactly the same illustrations as the left operand")
		else:
			_check(left_icons[0] != right_icons[0], "Addition mixes illustrations across operands")
		var stable_question: Dictionary = question.duplicate(true)
		_check(session.answer(-1).is_empty(), "Invalid arithmetic choice ignored")
		_check(not session.next_question() and session.current_index == index, "Cannot skip unanswered arithmetic question")
		_check(session.current_question() == stable_question, "Illustrations and choices remain stable while waiting")
		var selected := correct
		if index % 2 != 0:
			for value in choices:
				if value != correct:
					selected = value
					break
		var result: Dictionary = session.answer(selected)
		_check(result.get("is_correct") == (index % 2 == 0), "Arithmetic correctness")
		_check(session.is_answered(), "Arithmetic answer locks question")
		var score: int = session.correct_count
		_check(session.answer(correct).is_empty() and session.correct_count == score, "Arithmetic double-click cannot rescore")
		_check(session.current_question() == stable_question, "Feedback retains the exact illustration arrangement")
		_check(session.next_question() == (index == 9), "Arithmetic next only finishes at ten")
	_check(session.correct_count == 5 and session.is_finished(), "Arithmetic final score counts correct answers only")
	_check(session.answer(0).is_empty() and session.current_question().is_empty(), "Finished arithmetic rejects answers")


func _test_search(items: Array[Dictionary], backgrounds: Array, mode: String, habitats: Dictionary, habitat_backgrounds: Dictionary, seed_value: int) -> void:
	var session := SearchModel.new(_rng(seed_value))
	if not _check(session.start(items, backgrounds, mode, habitats, habitat_backgrounds), "Search start: %s" % session.error_message):
		return
	_check(session.total_questions() == 5, "Search always five questions")
	var targets: Dictionary = {}
	for index in range(5):
		var question: Dictionary = session.current_question()
		var target: Dictionary = question["target"]
		var target_key: String = target["key"]
		_check(not targets.has(target_key), "No target repeats within five search questions, in every subject")
		targets[target_key] = true
		_check(question["items"].size() == 3 and question["placements"].size() == 3, "Exactly one correct target and two distractors")
		_check(session.progress_text() == "もんだい %d / 5" % (index + 1), "Search progress label")
		_check(not session.next_question() and session.current_index == index, "Search cannot advance before finding target")
		_check(session.answer_at(Vector2(-1, 0.5)).is_empty(), "Outside-background click ignored")
		_check(session.answer_at(Vector2(0.5, 0.02)).is_empty(), "Empty-background click ignored")
		var species: Dictionary = {}
		var target_position := Vector2.ZERO
		var wrong_position := Vector2.ZERO
		var upper_height := 0.0
		var lower_height := 0.0
		for placement in question["placements"]:
			var key: String = placement["key"]
			var rect: Rect2 = placement["rect"]
			var hit_rect: Rect2 = placement["hit_rect"]
			_check(not species.has(key), "Hidden species are all distinct")
			species[key] = true
			_check(Rect2(Vector2.ZERO, Vector2.ONE).encloses(rect), "Sprite stays within background")
			_check(Rect2(Vector2.ZERO, Vector2.ONE).encloses(hit_rect), "Generous hit area stays within background")
			_check(hit_rect.encloses(rect), "Hit area fully contains illustration box")
			_check(hit_rect.size.is_equal_approx(rect.size * 2.0), "Hit area remains twice illustration box dimensions")
			_check(rect.size.x >= 0.12 and rect.size.x <= 0.16, "Search sprites remain small but visible")
			if rect.get_center().y < 0.3:
				upper_height = rect.size.y
			if rect.get_center().y > 0.7:
				lower_height = rect.size.y
			for other in question["placements"]:
				if other["key"] != key:
					_check(not hit_rect.intersects(other["hit_rect"]), "Hit areas do not overlap or mask another target")
			if key == target_key:
				target_position = hit_rect.position + hit_rect.size * Vector2(0.1, 0.1)
			else:
				wrong_position = hit_rect.get_center()
			if mode == "reconstruction":
				_check(habitats[key] == habitats[target_key], "Reconstruction distractors match target habitat")
		_check(species.has(target_key), "Named correct target is always hidden")
		_check(lower_height > upper_height, "Perspective makes lower sprites slightly larger")
		if mode == "reconstruction":
			_check(habitat_backgrounds[habitats[target_key]].has(question["background"]), "Dinosaur background matches target habitat")
		else:
			_check(backgrounds.has(question["background"]), "Search uses an approved background")
		var wrong: Dictionary = session.answer_at(wrong_position)
		_check(wrong.get("is_correct") == false and not session.is_answered(), "Wrong search click remains retryable")
		_check(session.found_count == index, "Wrong search clicks do not score")
		_check(not session.next_question() and session.current_index == index, "Wrong click cannot advance search")
		var correct: Dictionary = session.answer_at(target_position)
		_check(correct.get("is_correct") == true and session.is_answered(), "Generous edge of correct hit area works")
		_check(session.found_count == index + 1 and session.correct_count == index + 1, "Finding target scores exactly once")
		_check(session.answer_key(target_key).is_empty(), "Repeated correct click cannot replay result or rescore")
		_check(session.next_question() == (index == 4), "Search next only finishes after fifth find")
	_check(session.is_finished() and session.found_count == 5, "Search result is five of five")
	_check(session.answer_at(Vector2(0.5, 0.5)).is_empty(), "Finished search rejects clicks")


func _test_guards() -> void:
	var items := _sample_items()
	var arithmetic := ArithmeticModel.new(_rng(1))
	_check(not arithmetic.start(items, "multiply"), "Unsupported arithmetic operation rejected")
	_check(not arithmetic.start([], "addition"), "Missing arithmetic illustrations rejected")
	var duplicates: Array[Dictionary] = [items[0], items[0]]
	_check(not arithmetic.start(duplicates, "subtraction"), "Duplicate arithmetic illustration keys rejected")
	var search := SearchModel.new(_rng(1))
	_check(not search.start(items, ["forest"], "unknown"), "Unsupported search mode rejected")
	_check(not search.start([], ["forest"]), "Insufficient unique search targets rejected")
	_check(not search.start(items, []), "Missing search backgrounds rejected")
	_check(not search.start(items, [7]), "Non-string search background rejected")
	_check(not search.start(items, [], "reconstruction"), "Missing dinosaur habitat mapping rejected")
	_check(not search.start(duplicates, ["forest"]), "Duplicate search species rejected")
	_check(SearchModel.perspective_scale(0.0) < SearchModel.perspective_scale(1.0), "Perspective increases towards the lower background")
	_check(is_equal_approx(SearchModel.perspective_scale(-1.0), SearchModel.perspective_scale(0.0)), "Perspective upper edge clamped")
	_check(is_equal_approx(SearchModel.perspective_scale(2.0), SearchModel.perspective_scale(1.0)), "Perspective lower edge clamped")


func _test_seed_reproducibility() -> void:
	var items := _sample_items()
	for operation in ["addition", "subtraction"]:
		var first := ArithmeticModel.new(_rng(712))
		var second := ArithmeticModel.new(_rng(712))
		_check(first.start(items, operation) and second.start(items, operation), "Seeded arithmetic starts")
		_check(first.questions == second.questions, "Same RNG seed reproduces all arithmetic choices and illustrations")
	var first_search := SearchModel.new(_rng(712))
	var second_search := SearchModel.new(_rng(712))
	_check(first_search.start(items, ["forest_a", "forest_b"]) and second_search.start(items, ["forest_a", "forest_b"]), "Seeded search starts")
	_check(first_search.questions == second_search.questions, "Same RNG seed reproduces search targets, placement and backgrounds")


func _sample_items() -> Array[Dictionary]:
	var items: Array[Dictionary] = []
	for index in range(18):
		items.append({"key": "species_%d" % index, "name": "なまえ %d" % index})
	return items


func _rng(seed_value: int) -> RandomNumberGenerator:
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value
	return rng


func _check(condition: bool, message: String) -> bool:
	_checks += 1
	if not condition:
		_failures += 1
		push_error(message)
	return condition
