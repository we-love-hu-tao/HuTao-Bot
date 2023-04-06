from vkbottle.bot import BotLabeler, Message

from utils import translate

bl = BotLabeler()
bl.vbml_ignore_case = True


@bl.message(text=("!пинг", "!гнш пинг"))
async def do_ping(_: Message):
    return await translate("ping", "pong")
