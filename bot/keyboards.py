from vkbottle import Keyboard, Text

KEYBOARD_WISH = (
    Keyboard(inline=True)
    .add(Text("Помолиться 1 раз"))
    .row()
    .add(Text("Помолиться 10 раз"))
    .get_json()
)

