from vkbottle.bot import Blueprint, Message
from player_exists import exists
from loguru import logger
import create_pool
import random
import time

bp = Blueprint("Minigames")
bp.labeler.vbml_ignore_case = True


@bp.on.chat_message(text="!начать поручения")
async def start_daily_quests(message: Message):
    """
    Игрок сможет начать поручение только если:
    Он зарегестрирован;
    doing_quest == False
    daily_quests_time + 86400 секунд (24 часа) < текущего unix времени
    """
    if not await exists(message):
        return
    pool = create_pool.pool
    async with pool.acquire() as pool:
        result = await pool.fetchrow(
            "SELECT "
            "daily_quests_time, "
            "doing_quest "
            "FROM players WHERE user_id=$1 AND peer_id=$2",
            message.from_id, message.peer_id
        )
        daily_quests_time: int = result[0]
        doing_quest: int = result[1]

        if daily_quests_time + 86400 < int(time.time()) and doing_quest is False:
            logger.info(f"{message.from_id} начал поручения в беседе {message.peer_id}")
            await pool.execute(
                "UPDATE players SET "
                "daily_quests_time=$1, "
                "doing_quest=true "
                "WHERE user_id=$2 AND peer_id=$3",
                int(time.time()), message.from_id, message.peer_id,
            )
            await message.answer(
                "Вы начали выполнять поручения. "
                "Возвращайтесь через 20 минут!"
            )
        else:
            await message.answer(
                "Вы уже начали поручения или выполнили их!"
            )


@bp.on.chat_message(text="!закончить поручения")
async def complete_daily_quests(message: Message):
    """
    Игрок сможет закончить поручение только если:
        Он зарегестрирован;
        doing_quest == true;
        daily_quests_time + 1200 секунд (20 минут) < текущего unix времени
    """
    if not await exists(message):
        return
    pool = create_pool.pool
    async with pool.acquire() as pool:
        result = await pool.fetchrow(
            "SELECT "
            "daily_quests_time, "
            "doing_quest "
            "FROM players WHERE user_id=$1 AND peer_id=$2",
            message.from_id, message.peer_id
        )

        started_time: int = result[0]
        doing_quest: int = result[1]

        # 1200 - 20 минут
        if doing_quest and started_time + 1200 < int(time.time()):
            primogems_reward = random.randint(160, 1600)
            logger.info(f"{message.from_id} закончил поручения в беседе {message.peer_id}")
            await pool.execute(
                "UPDATE players SET "
                "doing_quest=false, "
                "primogems=primogems+$1 "
                "WHERE user_id=$2 ",
                primogems_reward, message.from_id,
            )

            await message.answer(
                "Вы выполнили поручения и получили "
                f"{primogems_reward} примогемов!"
            )
        else:
            await message.answer(
                "Еще не прошло 20 минут или сегодня вы уже выполнили все "
                "поручения!"
            )
