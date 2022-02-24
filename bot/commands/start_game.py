from vkbottle.bot import Blueprint, Message
import aiosqlite

bp = Blueprint("Start command")
bp.labeler.vbml_ignore_case = True


@bp.on.message(command="начать")
async def standard_wish(message: Message):
    async with aiosqlite.connect("db.db") as db:
        async with db.execute(
            "SELECT user_id FROM players WHERE user_id = (?)",
            (message.from_id,)
        ) as cursor:
            if await cursor.fetchone():
                await message.answer("Вы уже зашли в genshin impact")
            else:
                await db.execute(
                    "INSERT INTO players (user_id) VALUES (?)",
                    (message.from_id,)
                )
                await db.commit()
                await message.answer("Вы зашли в genshin impact")
