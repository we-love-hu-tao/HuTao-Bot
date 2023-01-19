import random
import time

from loguru import logger
from vkbottle.bot import BotLabeler, Message

import create_pool
from item_names import PRIMOGEM
from utils import exists, give_exp, give_item

bl = BotLabeler()
bl.vbml_ignore_case = True

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


@bl.message(text=(
    "!забрать награду",
    "!получить награду",
    "!награда",
    "[<!>|<!>] Награда",
    "Награда",
))
async def daily_reward(message: Message):
    if not await exists(message):
        return
    pool = create_pool.pool
    async with pool.acquire() as pool:
        reward_last_time = await pool.fetchrow(
            "SELECT reward_last_time FROM players "
            "WHERE user_id=$1 AND peer_id=$2",
            message.from_id, message.peer_id
        )

        # If more than 1 day lasted
        if int(time.time()) > reward_last_time[0] + 86400:
            # Updating time
            await pool.execute(
                "UPDATE players SET reward_last_time=$1 WHERE user_id=$2 AND peer_id=$3",
                int(time.time()), message.from_id, message.peer_id
            )

            if random.random() * 100 < 90:
                # Giving daily reward to a player
                reward_primogems = random.randint(160, 1600)
                reward_experience = random.randint(500, 1000)
                logger.info(
                    f"{message.from_id} получил {reward_primogems} "
                    f"примогемов в беседе {message.peer_id}"
                )
                await give_item(message.from_id, message.peer_id, PRIMOGEM, reward_primogems)
                await give_exp(reward_experience, message.from_id, message.peer_id, message.ctx_api)

                return random.choice(REWARD_ANSWERS).format(reward_primogems)
            else:
                # This guy is super unlucky, he got nothing
                return random.choice(NO_REWARD_ANSWERS)
        else:
            return "Вы уже попытались найти примогемы, попробуйте завтра!"
