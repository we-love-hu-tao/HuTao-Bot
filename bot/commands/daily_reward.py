<<<<<<< HEAD
from vkbottle.bot import Blueprint, Message
from player_exists import exists
import create_pool
import time
import random

bp = Blueprint("Daily reward")
bp.labeler.vbml_ignore_case = True

REWARD_ANSWERS = (
    "Вы проснулись, и увидели на своем столе {} примогемов!\n"
    "Интересно, как они там оказались?",
    "Вы вышли на улицу и нашли на земле {} примогемов",
    'Какой-то хиличурл нашел {} примогемов, и вы "одолжили" их у него'
)

NO_REWARD_ANSWERS = (
    "Сегодня вам не повезло, вы не нашли никаких примогемов...",
    "Пока вы шли домой, вы уронили все найденные примогемы в реку..."
)


@bp.on.chat_message(text=("!забрать награду", "!получить награду", "!награда"))
async def daily_reward(message: Message):
    pool = create_pool.pool
    async with pool.acquire() as pool:
        if not await exists(message, pool):
            return

        reward_last_time = await pool.fetchrow(
            """
            SELECT
            reward_last_time
            FROM players WHERE user_id=$1 AND
            peer_id=$2
            """,
            message.from_id, message.peer_id
        )

        # Если прошло больше 1 дня (24 часа)
        if int(time.time()) > reward_last_time[0] + 86400:
            # Обновляем время
            await pool.execute(
                "UPDATE players SET reward_last_time=$1 WHERE user_id=$2 AND peer_id=$3",
                int(time.time()), message.from_id, message.peer_id
            )

            if random.random() * 100 < 90:
                # Выдаем ежедневную награду игроку
                reward = random.randint(160, 1600)
                await pool.execute(
                    "UPDATE players SET primogems=primogems+$1 "
                    "WHERE user_id=$2 AND peer_id=$3",
                    reward, message.from_id, message.peer_id
                )

                await message.answer(random.choice(REWARD_ANSWERS).format(reward))
            else:
                await message.answer(random.choice(NO_REWARD_ANSWERS))
        else:
            await message.answer("Вы уже попытались найти примогемы, попробуйте завтра!")
