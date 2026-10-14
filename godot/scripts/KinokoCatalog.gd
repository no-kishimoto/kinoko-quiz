class_name KinokoCatalog
extends RefCounted
## Approved mushroom data and resource paths. No Python is used at runtime.

const DATA_PATH := "res://data/kinoko.json"
const EXPECTED_COUNT := 30
const TEXT_FIELDS := [
	"name", "habitat", "season", "size", "color", "features",
	"quiz_hint", "caution", "similar_kinoko", "trivia",
]
const TOXICITY_LABELS := {
	"poisonous": "どくあり",
	"non_poisonous": "どくなし",
	"unknown": "どくが あるか わかっていない",
}

var items: Array[Dictionary] = []
var error_message := ""
var _by_key: Dictionary = {}


func load_data() -> bool:
	items.clear()
	_by_key.clear()
	error_message = ""
	if not FileAccess.file_exists(DATA_PATH):
		return _fail("Missing mushroom data. Run the asset preparation step first.")
	var file := FileAccess.open(DATA_PATH, FileAccess.READ)
	if file == null:
		return _fail("Could not open mushroom data.")
	var parser := JSON.new()
	if parser.parse(file.get_as_text()) != OK:
		return _fail("Invalid mushroom JSON: %s" % parser.get_error_message())
	var raw: Variant = parser.data
	if not raw is Array or raw.size() != EXPECTED_COUNT:
		return _fail("Mushroom catalogue must contain exactly 30 entries.")
	var seen_names: Dictionary = {}
	var valid_key := RegEx.new()
	valid_key.compile("^[a-z][a-z0-9_]*$")
	for value in raw:
		if not value is Dictionary:
			return _fail("Each mushroom entry must be an object.")
		var item: Dictionary = value
		var key: Variant = item.get("key")
		if not key is String or valid_key.search(key) == null or _by_key.has(key):
			return _fail("Mushroom keys must be valid and unique.")
		for field in TEXT_FIELDS:
			var text: Variant = item.get(field)
			if not text is String or text.strip_edges().is_empty():
				return _fail("Mushroom %s is missing %s." % [key, field])
		if seen_names.has(item["name"]):
			return _fail("Mushroom names must be unique.")
		if not TOXICITY_LABELS.has(item.get("toxicity", "")):
			return _fail("Mushroom %s has invalid toxicity." % key)
		if item.get("edibility", "") not in ["edible", "not_edible", "unknown"]:
			return _fail("Mushroom %s has invalid edibility." % key)
		var cooking: Variant = item.get("cooking")
		if item["edibility"] == "edible":
			if not cooking is String or cooking.strip_edges().is_empty():
				return _fail("Edible mushroom %s needs cooking information." % key)
		elif cooking != null:
			return _fail("Only edible mushrooms may have cooking information.")
		if not ResourceLoader.exists(quiz_image_path(key)):
			return _fail("Missing quiz image for %s." % key)
		if not ResourceLoader.exists(color_image_path(key)):
			return _fail("Missing colour image for %s." % key)
		items.append(item)
		_by_key[key] = item
		seen_names[item["name"]] = true
	return true


func get_item(key: String) -> Dictionary:
	return _by_key.get(key, {})


func quiz_image_path(key: String) -> String:
	return "res://assets/images/quiz/%s.png" % key


func color_image_path(key: String) -> String:
	return "res://assets/images/zukan/%s.png" % key


func toxicity_text(item: Dictionary) -> String:
	return TOXICITY_LABELS.get(item.get("toxicity", "unknown"), TOXICITY_LABELS["unknown"])


func _fail(message: String) -> bool:
	items.clear()
	_by_key.clear()
	error_message = message
	return false
