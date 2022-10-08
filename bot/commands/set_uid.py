from vkbottle.bot import Blueprint, Message
from vkbottle.http import AiohttpClient
from player_exists import exists
from loguru import logger
from utils import get_default_header
import create_pool

bp = Blueprint("Set player in-game UID")


@bp.on.chat_message(text=(
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
        player_info = await http_client.request_json(
            f"https://enka.network/u/{UID}/__data.json",
            headers=get_default_header()
        )
    except Exception as e:
        logger.error(e)
        return (
            "Похоже, что сервис enka.network сейчас не работает!\n"
            "Если же это не так, пожалуйста, сообщите об этой ошибке [id322615766|мне]"
        )

    if len(player_info) == 0:
        return "Такого игрока не существует!"

    try:
        nickname = player_info['playerInfo']['nickname']
        adv_rank = player_info['playerInfo']['level']
        profile_picture = player_info['playerInfo']['profilePicture']
    except KeyError as e:
        logger.error(e)
        return "Похоже, что enka.network изменил свое апи, попробуйте позже"

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
