from vkbottle.bot import Blueprint, Message
import create_pool
import time

bp = Blueprint("Test ping")
bp.labeler.vbml_ignore_case = True


@bp.on.message(text=("!пинг", "!гнш пинг"))
async def do_ping(message: Message):
    command_start = time.time()
    pool = create_pool.pool

    time_db_connect = time.time()
    async with pool.acquire() as pool:
        await pool.fetch("SELECT * FROM players")
    time_db_connect_end = time.time()-time_db_connect

    command_end = time.time()-command_start
    return (
        f"Понг\nВремя выбора всего в базе данных: {round(time_db_connect_end, 2)}\n"
        f"Время команды: {round(command_end, 2)}"
    )
