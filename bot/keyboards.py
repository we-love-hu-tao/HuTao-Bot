from vkbottle import Keyboard, Text

KEYBOARD_START = (
    Keyboard(inline=True)
    .add(Text("Начать"))
    .get_json()
)

KEYBOARD_WISH = (
    Keyboard(inline=True)
    .add(Text("Помолиться 1 раз"))
    .row()
    .add(Text("Помолиться 10 раз"))
    .get_json()
)

# Выбор баннера
KEYBOARD_BEGINNER = (
    Keyboard(inline=True)
    .add(Text("Выбрать баннер новичка"))
    .get_json()
)
KEYBOARD_EVENT = (
    Keyboard(inline=True)
    .add(Text("Выбрать баннер ивент"))
    .get_json()
)
KEYBOARD_EVENT_SECOND = (
    Keyboard(inline=True)
    .add(Text("Выбрать баннер ивент 2"))
    .get_json()
)
KEYBOARD_WEAPON = (
    Keyboard(inline=True)
    .add(Text("Выбрать баннер оружие"))
    .get_json()
)
KEYBOARD_STANDARD = (
    Keyboard(inline=True)
    .add(Text("Выбрать баннер стандарт"))
    .get_json()
)
