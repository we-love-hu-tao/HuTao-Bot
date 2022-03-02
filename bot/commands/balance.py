from vkbottle.bot import Blueprint, Message
import aiosqlite

bp = Blueprint("Balance")
bp.labeler.vbml_ignore_case = True


@bp.on.message(command="молитвы")
async def balance(message: Message):
    async with aiosqlite.connect("db.db") as db:
        async with db.execute(
            "SELECT standard_wishes, event_wishes FROM players WHERE "
            "user_id=(?)",
            (message.from_id,),
        ) as cur:
            result = await cur.fetchone()
    if result:
        await message.answer(
            f"Судьбоносные встречи: {result[0]}\n"
            f"Переплетающиеся судьбы: {result[1]}"
        )
    else:
        await message.answer(
            "Для начала нужно зайти в genshin impact командой !начать"
        )
