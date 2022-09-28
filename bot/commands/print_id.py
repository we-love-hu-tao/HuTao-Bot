from vkbottle.bot import Blueprint, Message

bp = Blueprint("Print id")
bp.labeler.vbml_ignore_case = True


@bp.on.message(text=("!айди", "!id", "!ид", "!мой айди"))
async def print_id(message: Message):
    return f"Ваш айди: {message.from_id}\nАйди беседы: {message.peer_id}"
