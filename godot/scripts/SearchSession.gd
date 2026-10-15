class_name SearchSession
extends RefCounted
## Five nonrepeating targets and normalized, resize-independent hit areas.

const QUESTION_COUNT := 5

var questions: Array[Dictionary] = []
var current_index := 0
var found_count := 0
var correct_count := 0
var current_result: Dictionary = {}
var mode := "normal"
var error_message := ""
var _rng: RandomNumberGenerator


func _init(randomizer: RandomNumberGenerator = null) -> void:
	_rng = randomizer
	if _rng == null:
		_rng = RandomNumberGenerator.new()
		_rng.randomize()


func start(items: Array[Dictionary], backgrounds: Array, requested_mode: String = "normal", habitats: Dictionary = {}, habitat_backgrounds: Dictionary = {}) -> bool:
	questions.clear()
	current_index = 0
	found_count = 0
	correct_count = 0
	current_result = {}
	error_message = ""
	if requested_mode not in ["normal", "fossil", "reconstruction"]:
		return _fail("Unknown search mode.")
	if items.size() < QUESTION_COUNT:
		return _fail("Five distinct species are required for search.")
	var seen: Dictionary = {}
	var seen_names: Dictionary = {}
	for item in items:
		var key: Variant = item.get("key")
		var name: Variant = item.get("name")
		if not key is String or key.is_empty() or seen.has(key):
			return _fail("Search species keys must be nonempty and unique.")
		if not name is String or name.is_empty() or seen_names.has(name):
			return _fail("Search species names must be nonempty and unique.")
		seen[key] = true
		seen_names[name] = true
		if requested_mode == "reconstruction":
			var habitat: Variant = habitats.get(key)
			if habitat not in ["land", "sea"] or not _valid_backgrounds(habitat_backgrounds.get(habitat)):
				return _fail("Every reconstruction target requires approved habitat backgrounds.")
			var same_habitat_count := 0
			for candidate in items:
				if habitats.get(candidate.get("key")) == habitat:
					same_habitat_count += 1
			if same_habitat_count < 3:
				return _fail("Each reconstruction habitat needs at least three species.")
	if requested_mode != "reconstruction" and not _valid_backgrounds(backgrounds):
		return _fail("Search requires approved background images.")
	mode = requested_mode
	var targets: Array = items.duplicate()
	_shuffle(targets)
	for index in range(QUESTION_COUNT):
		var target: Dictionary = targets[index]
		var distractors: Array = []
		for item in items:
			if item["key"] == target["key"]:
				continue
			if mode == "reconstruction" and habitats[item["key"]] != habitats[target["key"]]:
				continue
			distractors.append(item)
		_shuffle(distractors)
		var hidden_items: Array = [target, distractors[0], distractors[1]]
		_shuffle(hidden_items)
		var candidates: Array = backgrounds
		if mode == "reconstruction":
			candidates = habitat_backgrounds[habitats[target["key"]]]
		var background: String = candidates[_rng.randi_range(0, candidates.size() - 1)]
		var placements: Array[Dictionary] = []
		var rows: Array = [0.25, 0.50, 0.75]
		_shuffle(rows)
		for slot in range(3):
			var y: float = rows[slot]
			var x: float = 0.18 + slot * 0.32 + _rng.randf_range(-0.01, 0.01)
			var sprite_size := Vector2(0.14, 0.21) * perspective_scale(y)
			var center := Vector2(x, y)
			placements.append({
				"key": hidden_items[slot]["key"],
				"rect": Rect2(center - sprite_size / 2.0, sprite_size),
				"hit_rect": Rect2(center - sprite_size, sprite_size * 2.0),
			})
		questions.append({
			"target": target, "items": hidden_items, "background": background,
			"placements": placements,
			"habitat": habitats.get(target["key"], "") if mode == "reconstruction" else "",
		})
	return true


static func perspective_scale(y: float) -> float:
	return 0.85 + 0.30 * clampf(y, 0.0, 1.0)


func total_questions() -> int:
	return questions.size()


func is_finished() -> bool:
	return current_index >= questions.size()


func is_answered() -> bool:
	return bool(current_result.get("is_correct", false))


func current_question() -> Dictionary:
	return {} if is_finished() else questions[current_index]


func progress_text() -> String:
	return "もんだい %d / %d" % [mini(current_index + 1, questions.size()), questions.size()]


func answer_at(position: Vector2) -> Dictionary:
	if is_finished() or is_answered() or not Rect2(Vector2.ZERO, Vector2.ONE).has_point(position):
		return {}
	for placement in current_question()["placements"]:
		var hit_rect: Rect2 = placement["hit_rect"]
		if hit_rect.has_point(position):
			return answer_key(placement["key"])
	return {}


func answer_key(selected_key: String) -> Dictionary:
	if is_finished() or is_answered():
		return {}
	var question := current_question()
	var is_present := false
	for item in question["items"]:
		if item["key"] == selected_key:
			is_present = true
			break
	if not is_present:
		return {}
	current_result = {
		"is_correct": selected_key == question["target"]["key"],
		"answer": question["target"], "selected_key": selected_key,
	}
	if current_result["is_correct"]:
		found_count += 1
		correct_count = found_count
	return current_result


func next_question() -> bool:
	if is_finished() or not is_answered():
		return is_finished()
	current_index += 1
	current_result = {}
	return is_finished()


func _valid_backgrounds(value: Variant) -> bool:
	if not value is Array or value.is_empty():
		return false
	for path in value:
		if not path is String or path.is_empty():
			return false
	return true


func _shuffle(values: Array) -> void:
	for index in range(values.size() - 1, 0, -1):
		var other := _rng.randi_range(0, index)
		var temporary: Variant = values[index]
		values[index] = values[other]
		values[other] = temporary


func _fail(message: String) -> bool:
	questions.clear()
	error_message = message
	return false
