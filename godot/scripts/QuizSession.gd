class_name QuizSession
extends RefCounted
## Pure quiz state. Pass a seeded RandomNumberGenerator for repeatable tests.

var questions: Array[Dictionary] = []
var current_index := 0
var correct_count := 0
var current_result: Dictionary = {}
var error_message := ""
var _rng: RandomNumberGenerator


func _init(randomizer: RandomNumberGenerator = null) -> void:
	if randomizer != null:
		_rng = randomizer
	else:
		_rng = RandomNumberGenerator.new()
		_rng.randomize()


func start(items: Array[Dictionary], question_count: int) -> bool:
	questions.clear()
	current_index = 0
	correct_count = 0
	current_result = {}
	error_message = ""
	if question_count not in [5, 10]:
		error_message = "Question count must be 5 or 10."
		return false
	if items.size() < question_count or items.size() < 3:
		error_message = "Not enough mushrooms for this quiz."
		return false
	var seen_keys: Dictionary = {}
	var seen_names: Dictionary = {}
	for item in items:
		var key: Variant = item.get("key")
		var name: Variant = item.get("name")
		if not key is String or key.is_empty() or seen_keys.has(key):
			error_message = "Mushroom keys must be nonempty and unique."
			return false
		if not name is String or name.is_empty() or seen_names.has(name):
			error_message = "Mushroom names must be nonempty and unique."
			return false
		seen_keys[key] = true
		seen_names[name] = true
	var pool: Array[Dictionary] = items.duplicate()
	_shuffle(pool)
	for question_index in range(question_count):
		var correct: Dictionary = pool[question_index]
		var distractors: Array[Dictionary] = []
		for candidate in items:
			if candidate["key"] != correct["key"]:
				distractors.append(candidate)
		_shuffle(distractors)
		var choices: Array[Dictionary] = [correct, distractors[0], distractors[1]]
		_shuffle(choices)
		questions.append({"answer": correct, "choices": choices})
	return true


func total_questions() -> int:
	return questions.size()


func is_finished() -> bool:
	return current_index >= questions.size()


func is_answered() -> bool:
	return not current_result.is_empty()


func current_question() -> Dictionary:
	if is_finished():
		return {}
	return questions[current_index]


func progress_text() -> String:
	return "もんだい %d / %d" % [mini(current_index + 1, questions.size()), questions.size()]


func answer(selected_key: String) -> Dictionary:
	if is_finished() or is_answered():
		return {}
	var question := current_question()
	var is_choice := false
	for choice in question["choices"]:
		if choice["key"] == selected_key:
			is_choice = true
			break
	if not is_choice:
		return {}
	var correct: Dictionary = question["answer"]
	current_result = {
		"is_correct": selected_key == correct["key"],
		"answer": correct,
		"selected_key": selected_key,
	}
	if current_result["is_correct"]:
		correct_count += 1
	return current_result


func next_question() -> bool:
	if is_finished() or not is_answered():
		return is_finished()
	current_index += 1
	current_result = {}
	return is_finished()


func _shuffle(values: Array[Dictionary]) -> void:
	for index in range(values.size() - 1, 0, -1):
		var other := _rng.randi_range(0, index)
		var temporary: Dictionary = values[index]
		values[index] = values[other]
		values[other] = temporary
