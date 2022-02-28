from vkbottle.bot import Blueprint, Message
import aiosqlite
import time

bp = Blueprint("Daily reward")
bp.labeler.vbml_ignore_case = True


@bp.on.message(command="получить награду")
async def daily_reward(message: Message):
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

        # Если игрок есть в боте
        if result:
            reward_last_time = result[0]
            standard_wishes = result[1]
            event_wishes = result[2]

            # Если прошло больше 1 дня (24 часа)
            if int(time.time()) > reward_last_time+86400:
                # Обновляем время
                await db.execute(
                    "UPDATE players SET reward_last_time=(?) WHERE "
                    "user_id=(?)",
                    (int(time.time()), message.from_id,),
                )
                await db.commit()

                # Выдаем ежедневную награду игроку
                await db.execute(
                    "UPDATE players SET standard_wishes=standard_wishes+5 "
                    "WHERE user_id=(?)",
                    (message.from_id,),
                )
                await db.execute(
                    "UPDATE players SET event_wishes=event_wishes+5 WHERE "
                    "user_id=(?)",
                    (message.from_id,),
                )
                await db.commit()

                await message.answer(
                    "Вы забрали ежедневную награду и теперь у вас "
                    f"{standard_wishes+5} судьбоносных встреч и "
                    f"{event_wishes+5} переплетающих судьб!"
                )
            else:
                await message.answer("Вы уже забирали ежедневную награду")
        else:
            await message.answer(
                "Для начала нужно зайти в genshin impact командой !начать"
            )
