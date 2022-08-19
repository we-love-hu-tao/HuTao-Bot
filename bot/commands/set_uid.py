from vkbottle.bot import Blueprint, Message
from vkbottle.http import AiohttpClient

bp = Blueprint("Set player in-game UID")


@bp.on.chat_message(text=("!установить айди", "!поменять айди"))
async def change_ingame_uid(message: Message):
    http_client = AiohttpClient()
    pass
