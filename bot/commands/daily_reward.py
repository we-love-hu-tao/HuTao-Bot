from vkbottle.bot import Blueprint, Message
from player_exists import exists
import aiosqlite
import time

bp = Blueprint("Daily reward")
bp.labeler.vbml_ignore_case = True


@bp.on.message(text=("!забрать награду", "!получить награду", "!награда"))
async def daily_reward(message: Message):
    if not await exists(message):
        return
    async with aiosqlite.connect("db.db") as db:
        async with db.execute(
            """SELECT
            reward_last_time,
            standard_wishes,
            event_wishes
            FROM players WHERE user_id=(?)""",
            (message.from_id,),
        ) as cur:
            result = await cur.fetchone()

        reward_last_time = result[0]
        standard_wishes = result[1]
        event_wishes = result[2]

        # Если прошло больше 1 дня (24 часа)
        if int(time.time()) > reward_last_time + 86400:
            # Обновляем время
            await db.execute(
                "UPDATE players SET reward_last_time=(?) WHERE user_id=(?)",
                (
                    int(time.time()),
                    message.from_id,
                ),
            )
            await db.commit()

            # Выдаем ежедневную награду игроку
            await db.execute(
                "UPDATE players SET standard_wishes=standard_wishes+10 "
                "WHERE user_id=(?)",
                (message.from_id,),
            )
            await db.execute(
                "UPDATE players SET event_wishes=event_wishes+10 WHERE "
                "user_id=(?)",
                (message.from_id,),
            )
            await db.commit()

            await message.answer(
                "Вы забрали ежедневную награду и теперь у вас "
                f"{standard_wishes+10} судьбоносных встреч и "
                f"{event_wishes+10} переплетающих судьб!"
            )
        else:
            await message.answer("Вы уже забирали ежедневную награду")
