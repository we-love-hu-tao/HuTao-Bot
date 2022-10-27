import time

from vkbottle.bot import Blueprint, Message

bp = Blueprint("Test ping")
bp.labeler.vbml_ignore_case = True


@bp.on.message(text=("!пинг", "!гнш пинг"))
async def do_ping(message: Message):
    command_start = time.time()
    command_end = time.time()-command_start
    return (
        f"Понг\n"
        f"Время команды: {round(command_end, 2)}"
    )
