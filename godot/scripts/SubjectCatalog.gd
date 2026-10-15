class_name SubjectCatalog
extends RefCounted
## Runtime-only catalogue. The preparation tool copies approved RGBA assets as-is.

const DATA_PATH := "res://data/game_catalog.json"
const EXPECTED_COUNTS := {"kinoko": 30, "shokubutsu": 40, "konchuu": 29, "kyouryuu": 18}
const TOXICITY_LABELS := {
	"poisonous": "どくあり",
	"non_poisonous": "どくなし",
	"unknown": "どくが あるか わかっていない",
}

var subjects: Dictionary = {}
var subject_id := "kinoko"
var label := "きのこ"
var items: Array[Dictionary] = []
var error_message := ""
var _by_key: Dictionary = {}


func load_data() -> bool:
	subjects.clear()
	items.clear()
	_by_key.clear()
	error_message = ""
	if not FileAccess.file_exists(DATA_PATH):
		return _fail("Missing game catalogue. Run the asset preparation step first.")
	var file := FileAccess.open(DATA_PATH, FileAccess.READ)
	if file == null:
		return _fail("Could not open the game catalogue.")
	var parser := JSON.new()
	if parser.parse(file.get_as_text()) != OK:
		return _fail("Invalid game catalogue JSON: %s" % parser.get_error_message())
	var data: Variant = parser.data
	if not data is Dictionary or data.get("format_version") != 1 or data.get("species_count") != 117:
		return _fail("The game catalogue format or total species count is invalid.")
	var raw_subjects: Variant = data.get("subjects")
	if not raw_subjects is Dictionary or raw_subjects.size() != EXPECTED_COUNTS.size():
		return _fail("The game catalogue must contain all four subjects.")
	for identifier in EXPECTED_COUNTS:
		var subject: Variant = raw_subjects.get(identifier)
		if not subject is Dictionary:
			return _fail("Missing subject: %s" % identifier)
		if not subject.get("label") is String or str(subject["label"]).strip_edges().is_empty():
			return _fail("Subject %s needs a display label." % identifier)
		var records: Variant = subject.get("items")
		if not records is Array or records.size() != EXPECTED_COUNTS[identifier]:
			return _fail("Unexpected species count for %s." % identifier)
		var seen_keys: Dictionary = {}
		var seen_names: Dictionary = {}
		for record in records:
			if not record is Dictionary:
				return _fail("Every catalogue entry must be an object.")
			var key: Variant = record.get("key")
			var name: Variant = record.get("name")
			if not key is String or key.is_empty() or seen_keys.has(key):
				return _fail("Species keys must be nonempty and unique within each subject.")
			if not name is String or name.strip_edges().is_empty() or seen_names.has(name):
				return _fail("Species names must be nonempty and unique within each subject.")
			for field in ["quiz_hint", "quiz_image", "color_image", "search_image"]:
				if not record.get(field) is String or str(record[field]).strip_edges().is_empty():
					return _fail("Species %s is missing %s." % [key, field])
			for field in ["quiz_image", "color_image", "search_image"]:
				if not _is_resource(record[field]):
					return _fail("Missing %s for %s." % [field, key])
			if identifier == "kyouryuu" and not _is_resource(record.get("fossil_image", "")):
				return _fail("Missing fossil image for %s." % key)
			if identifier == "kinoko":
				for field in ["habitat", "season", "size", "color", "features", "caution", "similar_kinoko", "trivia"]:
					if not record.get(field) is String or str(record[field]).strip_edges().is_empty():
						return _fail("Mushroom %s is missing %s." % [key, field])
				if not TOXICITY_LABELS.has(record.get("toxicity", "")):
					return _fail("Invalid mushroom toxicity: %s." % key)
				if record.get("edibility", "") not in ["edible", "not_edible", "unknown"]:
					return _fail("Invalid mushroom edibility: %s." % key)
				if record["edibility"] == "edible":
					if not record.get("cooking") is String or str(record["cooking"]).strip_edges().is_empty():
						return _fail("Edible mushrooms need cooking information: %s." % key)
				elif record.get("cooking") != null:
					return _fail("Only edible mushrooms may have cooking information.")
			elif not record.get("zukan_text") is String or str(record["zukan_text"]).strip_edges().is_empty():
				return _fail("Missing encyclopedia explanation: %s." % key)
			seen_keys[key] = true
			seen_names[name] = true
		if identifier == "kyouryuu":
			if not _validate_backgrounds(subject.get("fossil_backgrounds"), 2):
				return _fail("The fossil search requires the two approved backgrounds.")
			var habitats: Variant = subject.get("habitats")
			var habitat_backgrounds: Variant = subject.get("habitat_backgrounds")
			if not habitats is Dictionary or not habitat_backgrounds is Dictionary:
				return _fail("Missing dinosaur search habitat mapping.")
			if not _validate_backgrounds(habitat_backgrounds.get("land"), 2) or not _validate_backgrounds(habitat_backgrounds.get("sea"), 1):
				return _fail("Missing approved dinosaur habitat backgrounds.")
			for key in seen_keys:
				if habitats.get(key) not in ["land", "sea"]:
					return _fail("Unknown dinosaur habitat for %s." % key)
		elif not _validate_backgrounds(subject.get("backgrounds"), 4):
			return _fail("The forest search requires all four approved backgrounds.")
		subjects[identifier] = subject
	return select_subject("kinoko")


func select_subject(identifier: String) -> bool:
	if not subjects.has(identifier):
		error_message = "Unknown subject: %s" % identifier
		return false
	subject_id = identifier
	label = subjects[identifier]["label"]
	items.clear()
	_by_key.clear()
	for record in subjects[identifier]["items"]:
		items.append(record)
		_by_key[record["key"]] = record
	error_message = ""
	return true


func get_item(key: String) -> Dictionary:
	return _by_key.get(key, {})


func quiz_image_path(key: String) -> String:
	return str(get_item(key).get("quiz_image", ""))


func color_image_path(key: String) -> String:
	return str(get_item(key).get("color_image", ""))


func search_image_path(key: String, mode: String = "normal") -> String:
	var record := get_item(key)
	if mode == "fossil":
		return str(record.get("fossil_image", ""))
	return str(record.get("search_image", record.get("color_image", "")))


func toxicity_text(item: Dictionary) -> String:
	return TOXICITY_LABELS.get(item.get("toxicity", "unknown"), TOXICITY_LABELS["unknown"])


func _validate_backgrounds(value: Variant, expected: int) -> bool:
	if not value is Array or value.size() != expected:
		return false
	var seen: Dictionary = {}
	for path in value:
		if not _is_resource(path) or seen.has(path):
			return false
		seen[path] = true
	return true


func _is_resource(value: Variant) -> bool:
	return value is String and value.begins_with("res://assets/") and ResourceLoader.exists(value)


func _fail(message: String) -> bool:
	subjects.clear()
	items.clear()
	_by_key.clear()
	error_message = message
	return false
