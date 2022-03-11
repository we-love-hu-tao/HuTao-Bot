from vkbottle.bot import Blueprint, Message
import aiosqlite

bp = Blueprint('Profile')
bp.labeler.vbml_ignore_case = True


@bp.on.message(text=("!персонаж", "!перс"))
async def profile(message: Message):
    async with aiosqlite.connect("db.db") as db:
        async with db.execute(
            "SELECT "
            "nickname, "
            "standard_wishes, "
            "event_wishes, "
            "legendary_rolls_standard, "
            "legendary_rolls_event "
            "FROM players WHERE user_id=(?)", (message.from_id,)
        ) as cur:
            result = await cur.fetchone()

    if not result:
        await message.answer("Для начала нужно зайти в Genshin Impact командой !начать")
        return
    nickname = result[0]
    standard_wishes = result[1]
    event_wishes = result[2]
    legendary_standard_guarantee = result[3]
    legendary_event_guarantee = result[4]

    await message.answer(
        f"Ник: {nickname}\n"
        f"Стандартных молитв: {standard_wishes}\n"
        f"Молитв события: {event_wishes}\n\n"
        f"Открытых стандартных молитв без 5 звездочного предмета: {legendary_standard_guarantee}\n\n"
        f"Открытых ивентовых молитв без 5 звездочного предмета: {legendary_event_guarantee}"
    )
    