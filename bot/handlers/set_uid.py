from loguru import logger
from vkbottle.bot import BotLabeler, Message
from vkbottle.http import AiohttpClient

import create_pool
from config import ADMIN_IDS
from utils import exists, get_player_info, translate

bl = BotLabeler()


@bl.message(text=(
    "!установить айди <uid:int>",
    "!поменять айди <uid:int>",
    "!айди <uid:int>",
    "!ид <uid:int>"
))
async def change_ingame_uid(message: Message, uid: int):
    if not await exists(message):
        return

    http_client = AiohttpClient()
    try:
        player_info = await get_player_info(http_client, uid)
    except Exception as e:
        logger.error(e)
        return (await translate("set_uid", "enka_network_error")).format(user_id=ADMIN_IDS[0])

    if not player_info:
        return await translate("set_uid", "player_not_found")
    player_info = player_info.player_info

    nickname = player_info.nickname or await translate("set_uid", "unknown_nickname")
    adv_rank = player_info.level or await translate("set_uid", "unknown_adv_rank")
    profile_picture = player_info.profile_picture.avatar_id

    pool = create_pool.pool
    async with pool.acquire() as pool:
        await pool.execute(
            "UPDATE players SET uid=$1 WHERE user_id=$2 AND peer_id=$3",
            uid, message.from_id, message.peer_id
        )

    text = (
        await translate("set_uid", "set_success")
    ).format(nickname=nickname, adv_rank=adv_rank)
    if profile_picture == 10000046:
        text += "\n" + await translate("set_uid", "HuTao_easter_egg")

    return text
