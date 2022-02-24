from vkbottle.bot import Blueprint, Message
import aiosqlite

bp = Blueprint("Get wishes command")
bp.labeler.vbml_ignore_case = True


@bp.on.message(command="ст м")
async def give_standard_wish(message: Message):
    async with aiosqlite.connect("db.db") as db:
        async with db.execute(
            "SELECT standard_wishes FROM players WHERE user_id = (?)",
            (message.from_id,),
        ) as cur:
            exists = await cur.fetchone()
            if exists:
                await db.execute(
                    "UPDATE players SET standard_wishes=standard_wishes+5 "
                    "WHERE user_id=(?)",
                    (message.from_id,),
                )
                await db.commit()
                await message.answer(f"Ок! ({exists[0] + 5})")
            else:
                await message.answer(
                    "Для начала нужно зайти в genshin impact командой !начать"
                )


@bp.on.message(command="ив м")
async def give_event_wish(message: Message):
    async with aiosqlite.connect("db.db") as db:
        async with db.execute(
            "SELECT event_wishes FROM players WHERE user_id = (?)",
            (message.from_id,),
        ) as cur:
            exists = await cur.fetchone()
            if exists:
                await db.execute(
                    "UPDATE players SET event_wishes=event_wishes+5 WHERE "
                    "user_id=(?)",
                    (message.from_id,),
                )
                await db.commit()
                await message.answer(f"Ок! ({exists[0] + 5})")
            else:
                await message.answer(
                    "Для начала нужно зайти в genshin impact командой !начать"
                )
