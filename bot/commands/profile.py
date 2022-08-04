from vkbottle.bot import Blueprint, Message
from player_exists import exists
import asyncpg

bp = Blueprint("Profile")
bp.labeler.vbml_ignore_case = True


@bp.on.message(text=("!персонаж", "!перс"))
async def profile(message: Message):
    async with asyncpg.create_pool(
        user="postgres", database="genshin_bot", passfile="pgpass.conf"
    ) as pool:
        async with pool.acquire() as db:
            if not await exists(message, db):
                return
            result = await db.fetchrow(
                "SELECT "
                "nickname, "
                "primogems, "
                "standard_wishes, "
                "event_wishes, "
                "legendary_rolls_standard, "
                "legendary_rolls_event "
                "FROM players WHERE user_id=$1 and peer_id=$2",
                message.from_id, message.peer_id
            )

    print(result)
    nickname = result["nickname"]
    primogems = result["primogems"]
    standard_wishes = result["standard_wishes"]
    event_wishes = result["event_wishes"]
    legendary_standard_guarantee = result["legendary_rolls_standard"]
    legendary_event_guarantee = result["legendary_rolls_event"]

    await message.answer(
        f"Ник: {nickname}\nПримогемы: {primogems}\nСтандартных молитв: "
        f"{standard_wishes}\nМолитв события: {event_wishes}\n\nГарант в "
        f"стандартном баннере: {legendary_standard_guarantee}\n\nГарант в "
        f"ивентовом баннере: {legendary_event_guarantee}"
    )
