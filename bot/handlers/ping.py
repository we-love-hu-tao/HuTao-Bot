import time

from vkbottle.bot import BotLabeler, Message, rules

bl = BotLabeler()
bl.vbml_ignore_case = True


@bl.message(text=("!пинг", "!гнш пинг"))
async def do_ping(message: Message):
    command_start = time.time()
    command_end = time.time()-command_start
    return (
        f"Понг\n"
        f"Время команды: {round(command_end, 2)}"
    )
