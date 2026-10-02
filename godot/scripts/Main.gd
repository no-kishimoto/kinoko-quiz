extends Control

const SUBJECTS := [
	{"icon": "🍄", "name": "きのこ"},
	{"icon": "🌱", "name": "しょくぶつ"},
	{"icon": "🪲", "name": "こんちゅう"},
]

var heading: Label
var message: Label
var menu: VBoxContainer


func _ready() -> void:
	_build_title()


func _build_title() -> void:
	_clear_screen()
	heading = _label("なにで あそぶ？", 52)
	heading.set_anchors_preset(Control.PRESET_CENTER_TOP)
	heading.position.y = 80
	add_child(heading)

	menu = VBoxContainer.new()
	menu.add_theme_constant_override("separation", 24)
	menu.set_anchors_preset(Control.PRESET_CENTER)
	menu.position = Vector2(-210, -115)
	menu.size = Vector2(420, 260)
	add_child(menu)
	for subject in SUBJECTS:
		var button := _button("%s  %s" % [subject.icon, subject.name])
		button.pressed.connect(_choose_subject.bind(subject))
		menu.add_child(button)


func _choose_subject(subject: Dictionary) -> void:
	_clear_screen()
	heading = _label("%s %sクイズ" % [subject.icon, subject.name], 48)
	heading.set_anchors_preset(Control.PRESET_CENTER_TOP)
	heading.position.y = 70
	add_child(heading)

	menu = VBoxContainer.new()
	menu.add_theme_constant_override("separation", 18)
	menu.set_anchors_preset(Control.PRESET_CENTER)
	menu.position = Vector2(-230, -175)
	menu.size = Vector2(460, 400)
	add_child(menu)
	for title in ["クイズで あそぶ", "たしざんで あそぶ", "ひきざんで あそぶ", "%s さがし" % subject.name, "%s ずかん を みる" % subject.name]:
		var button := _button(title)
		button.disabled = true
		menu.add_child(button)

	message = _label("Godotばんを つくっているよ。", 24)
	message.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	message.position.y = -105
	add_child(message)
	var back := _button("なかまを えらびなおす")
	back.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	back.position = Vector2(-210, -70)
	back.pressed.connect(_build_title)
	add_child(back)


func _clear_screen() -> void:
	for child in get_children():
		child.queue_free()
	var background := ColorRect.new()
	background.color = Color("fff8dc")
	background.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(background)


func _label(text: String, font_size: int) -> Label:
	var label := Label.new()
	label.text = text
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.add_theme_color_override("font_color", Color("202020"))
	label.add_theme_font_size_override("font_size", font_size)
	label.size = Vector2(700, 80)
	return label


func _button(text: String) -> Button:
	var button := Button.new()
	button.text = text
	button.custom_minimum_size = Vector2(420, 62)
	button.add_theme_font_size_override("font_size", 28)
	return button
