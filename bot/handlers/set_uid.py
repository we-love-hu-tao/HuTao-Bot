from loguru import logger
from vkbottle.bot import BotLabeler, Message, rules
from vkbottle.http import AiohttpClient

import create_pool
from utils import exists, get_player_info

bl = BotLabeler()


@bl.message(text=(
    "!установить айди <UID:int>",
    "!поменять айди <UID:int>",
    "!айди <UID:int>",
    "!ид <UID:int>"
))
async def change_ingame_uid(message: Message, UID: int):
    if not await exists(message):
        return

    http_client = AiohttpClient()
    try:
        player_info = await get_player_info(http_client, UID)
    except Exception as e:
        logger.error(e)
        return (
            "Похоже, что сервис enka.network сейчас не работает!\n"
            "Если же это не так, пожалуйста, сообщите об этой ошибке [id322615766|мне]"
        )

    if not player_info:
        return "Такого игрока не существует!"

    nickname = player_info.nickname or "неизвестный ник"
    adv_rank = player_info.level or "неизвестный"
    profile_picture = player_info.profile_picture.avatar_id

    pool = create_pool.pool
    async with pool.acquire() as pool:
        await pool.execute(
            "UPDATE players SET uid=$1 WHERE user_id=$2 AND peer_id=$3",
            UID, message.from_id, message.peer_id
        )

    text = (
        f'Вы успешно установили UID игрока "{nickname}" '
        f'(AR: {adv_rank})'
    )
    if profile_picture == 10000046:
        text += "\nХу Тао на аве, здоровья маме"

    return text

