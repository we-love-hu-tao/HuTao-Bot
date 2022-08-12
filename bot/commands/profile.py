from vkbottle.bot import Blueprint, Message
from player_exists import exists
import create_pool

bp = Blueprint("Profile")
bp.labeler.vbml_ignore_case = True


@bp.on.chat_message(text=("!персонаж", "!перс"))
async def profile(message: Message):
    pool = create_pool.pool
    async with pool.acquire() as pool:
        if not await exists(message, pool):
            return
        result = await pool.fetchrow(
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

    nickname = result["nickname"]
    primogems = result["primogems"]
    standard_wishes = result["standard_wishes"]
    event_wishes = result["event_wishes"]
    legendary_standard_guarantee = result["legendary_rolls_standard"]
    legendary_event_guarantee = result["legendary_rolls_event"]

    return (
        f"&#128100; Ник: {nickname}\n"
        f"&#129689; Примогемы: {primogems}\n"
        f"&#127852; Стандартных молитв: {standard_wishes}\n"
        f"&#127846; Молитв события: {event_wishes}\n\n"

        f"&#10133; Гарант в стандартном баннере: {legendary_standard_guarantee}\n"
        f"&#10133; Гарант в ивентовом баннере: {legendary_event_guarantee}"
    )
