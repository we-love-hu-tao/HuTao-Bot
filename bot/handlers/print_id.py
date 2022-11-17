from vkbottle.bot import BotLabeler, Message

bl = BotLabeler()
bl.vbml_ignore_case = True


@bl.message(text=("!айди", "!id", "!ид", "!мой айди"))
async def print_id(message: Message):
    return f"Ваш айди: {message.from_id}\nАйди беседы: {message.peer_id}"
