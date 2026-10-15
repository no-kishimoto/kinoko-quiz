extends Control
## A single display/input surface; the same letterboxed rectangle drives both.

signal picked(point: Vector2)

var _question: Dictionary = {}
var _background: Texture2D
var _sprites: Dictionary = {}
var _revealed := false


func configure(question: Dictionary, catalog: RefCounted, mode: String) -> void:
	_question = question
	_background = load(question["background"]) as Texture2D
	_sprites.clear()
	for item in question["items"]:
		_sprites[item["key"]] = load(catalog.search_image_path(item["key"], mode)) as Texture2D
	mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	queue_redraw()


func content_rect() -> Rect2:
	if _background == null or size.x <= 0 or size.y <= 0:
		return Rect2()
	var source := _background.get_size()
	var scale_factor := minf(size.x / source.x, size.y / source.y)
	var drawn_size := source * scale_factor
	return Rect2((size - drawn_size) / 2, drawn_size)


func normalized_to_local(point: Vector2) -> Vector2:
	var frame := content_rect()
	return frame.position + point * frame.size


func local_to_normalized(point: Vector2) -> Vector2:
	var frame := content_rect()
	if frame.size.x <= 0 or frame.size.y <= 0 or not frame.has_point(point):
		return Vector2(-1, -1)
	return (point - frame.position) / frame.size


func reveal_target() -> void:
	_revealed = true
	queue_redraw()


func _notification(what: int) -> void:
	if what == NOTIFICATION_RESIZED:
		queue_redraw()


func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT and event.pressed:
		var point := local_to_normalized(event.position)
		if point.x >= 0:
			picked.emit(point)
			accept_event()


func _draw() -> void:
	if _background == null:
		return
	var frame := content_rect()
	draw_texture_rect(_background, frame, false)
	for placement in _question["placements"]:
		var image: Texture2D = _sprites[placement["key"]]
		var normalized: Rect2 = placement["rect"]
		var box := Rect2(frame.position + normalized.position * frame.size, normalized.size * frame.size)
		var image_scale := minf(box.size.x / image.get_width(), box.size.y / image.get_height())
		var drawn_size := image.get_size() * image_scale
		# Render original RGBA directly: no blue/white colour-key transparency.
		draw_texture_rect(image, Rect2(box.get_center() - drawn_size / 2, drawn_size), false)
		if _revealed and placement["key"] == _question["target"]["key"]:
			var radius := maxf(box.size.x, box.size.y) * 0.58
			draw_arc(box.get_center(), radius, 0, TAU, 72, Color.WHITE, 8, true)
			draw_arc(box.get_center(), radius, 0, TAU, 72, Color("ffa21a"), 4, true)
