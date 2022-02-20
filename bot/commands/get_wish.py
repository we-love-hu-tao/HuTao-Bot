from vkbottle.bot import Blueprint, Message
import aiosqlite

bp = Blueprint("Get wishes command")
bp.labeler.vbml_ignore_case = True

@bp.on.message(command="ст м")
async def give_wish(message: Message):
    async with aiosqlite.connect("db.db") as db:
        async with db.execute("SELECT user_id FROM players WHERE user_id = (?)", (message.from_id,)) as cur:
            exists = await cur.fetchone()
            if exists:
                await db.execute(f"UPDATE players SET standart_wishes=standart_wishes+5 WHERE user_id=(?)", (message.from_id,))
                await db.commit()
                await message.answer("Ок! (+5)")
            else:
                await message.answer("Для начала нужно зайти в genshin impact командой !начать")