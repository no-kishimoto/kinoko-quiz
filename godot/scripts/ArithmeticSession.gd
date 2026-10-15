class_name ArithmeticSession
extends RefCounted
## Ten stable questions, with illustrated and numeral-only learning stages.

const KANJI_NUMERALS := ["〇", "一", "二", "三", "四", "五", "六", "七", "八", "九"]
const QUESTION_COUNT := 10

var questions: Array[Dictionary] = []
var current_index := 0
var correct_count := 0
var current_result: Dictionary = {}
var operation := "addition"
var error_message := ""
var _rng: RandomNumberGenerator


func _init(randomizer: RandomNumberGenerator = null) -> void:
	_rng = randomizer
	if _rng == null:
		_rng = RandomNumberGenerator.new()
		_rng.randomize()


func start(items: Array[Dictionary], requested_operation: String) -> bool:
	questions.clear()
	current_index = 0
	correct_count = 0
	current_result = {}
	error_message = ""
	if requested_operation not in ["addition", "subtraction"]:
		return _fail("Arithmetic operation must be addition or subtraction.")
	var keys: Array[String] = []
	for item in items:
		var key: Variant = item.get("key")
		if not key is String or key.is_empty() or keys.has(key):
			return _fail("Illustration keys must be nonempty and unique.")
		keys.append(key)
	if keys.size() < 2:
		return _fail("Arithmetic needs at least two approved illustration species.")
	operation = requested_operation
	var pairs: Array = []
	for left in range(1, 10):
		for right in range(1, 10):
			if operation == "addition" and left <= 8 and right <= 8 and left + right <= 9:
				pairs.append({"left": left, "right": right, "answer": left + right})
			elif operation == "subtraction" and right <= left:
				pairs.append({"left": left, "right": right, "answer": left - right})
	_shuffle(pairs)
	for index in range(QUESTION_COUNT):
		var pair: Dictionary = pairs[index]
		var left_count: int = pair["left"]
		var right_count: int = pair["right"]
		var answer_value: int = pair["answer"]
		var illustration_pool: Array = keys.duplicate()
		_shuffle(illustration_pool)
		var left_icons: Array[String] = []
		var right_icons: Array[String] = []
		for icon_index in range(left_count):
			left_icons.append(illustration_pool[icon_index % illustration_pool.size()])
		if operation == "subtraction":
			# The right operand shows the exact same kinds being taken from the left.
			for icon_index in range(right_count):
				right_icons.append(left_icons[icon_index])
		else:
			for icon_index in range(right_count):
				right_icons.append(illustration_pool[(left_count + icon_index) % illustration_pool.size()])
		var distractors: Array = []
		for value in range(10):
			if value != answer_value:
				distractors.append(value)
		_shuffle(distractors)
		var choices: Array = [answer_value, distractors[0], distractors[1]]
		_shuffle(choices)
		questions.append({
			"left": left_count, "right": right_count, "answer": answer_value,
			"choices": choices, "left_icons": left_icons, "right_icons": right_icons,
		})
	return true


func total_questions() -> int:
	return questions.size()


func is_finished() -> bool:
	return current_index >= questions.size()


func is_answered() -> bool:
	return not current_result.is_empty()


func current_question() -> Dictionary:
	return {} if is_finished() else questions[current_index]


func progress_text() -> String:
	return "もんだい %d / %d" % [mini(current_index + 1, questions.size()), questions.size()]


func shows_icons() -> bool:
	return not is_finished() and (current_index < 4 or current_index >= 7)


func uses_kanji_numerals() -> bool:
	return not is_finished() and current_index >= 7


func display_number(value: int) -> String:
	if uses_kanji_numerals() and value >= 0 and value < KANJI_NUMERALS.size():
		return KANJI_NUMERALS[value]
	return str(value)


func answer(selected_value: int) -> Dictionary:
	if is_finished() or is_answered():
		return {}
	var question := current_question()
	if not question["choices"].has(selected_value):
		return {}
	current_result = {
		"is_correct": selected_value == question["answer"],
		"answer": question["answer"], "selected_value": selected_value,
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
