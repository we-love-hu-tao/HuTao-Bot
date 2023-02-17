from typing import Optional

from loguru import logger
from vkbottle import Callback, GroupEventType, Keyboard
from vkbottle import KeyboardButtonColor as Color
from vkbottle.bot import BotLabeler, Message, MessageEvent, rules
from vkbottle.http import AiohttpClient

import create_pool
from utils import get_avatar_data, get_player_info, get_textmap, resolve_id, resolve_map_hash
from variables import FAV_AVATARS

bl = BotLabeler()
bl.vbml_ignore_case = True

http_client = AiohttpClient()


@bl.message(
    text=("!геншин инфо", "!геншин инфо <UID:int>", "! геншин инфо", " ! геншин инфо <UID:int>")
)
async def genshin_info(message: Message, UID: Optional[int] = None):
    info_msg = ""

    if UID is None:
        pool = create_pool.pool
        async with pool.acquire() as pool:
            if message.reply_message is None:
                UID = await pool.fetchrow(
                    "SELECT uid FROM players WHERE user_id=$1 AND peer_id=$2",
                    message.from_id,
                    message.peer_id,
                )

                if UID is None or UID["uid"] is None:
                    return (
                        "Вы не установили свой UID! "
                        'Его можно установить с помощью команды "!установить айди <UID>"'
                    )
            else:
                UID = await pool.fetchrow(
                    "SELECT uid FROM players WHERE user_id=$1 AND peer_id=$2",
                    message.reply_message.from_id,
                    message.peer_id,
                )

                if UID is None or UID["uid"] is None:
                    return (
                        "Человек, на которого вы ответили, еще не создал аккаунт "
                        "/ не указал айди, однако он может это сделать, написав "
                        '"!установить айди <UID>"'
                    )
                info_msg += (
                    f"Информация об аккаунте [id{message.reply_message.from_id}|этого] игрока\n\n"
                )

            UID = UID["uid"]

    try:
        player_info = (await get_player_info(http_client, UID, only_info=True)).player_info
    except Exception as e:
        logger.error(e)
        return (
            "Похоже, что сервис enka.network сейчас не работает!\n"
            "Если же это не так, пожалуйста, сообщите об этой ошибке [id322615766|мне]"
        )

    if not player_info:
        if UID is None:
            return (
                "Ээээ... Информацию об этом UID не получилось найти, "
                "похоже этот аккаунт в геншине был забанен/удален\n"
                "(или это ошибка enka.network)"
            )
        else:
            return "Игрока с таким UID не существует!"

    nickname = player_info.nickname or "неизвестный"
    adv_rank = player_info.level or "неизвестный"
    signature = player_info.signature or "нету"
    world_level = player_info.world_level or "неизвестен"
    profile_picture = player_info.profile_picture.avatar_id or 0
    show_avatars = player_info.show_avatar_info_list or None

    avatar_data = await get_avatar_data()
    textmap = await get_textmap()
    avatar_picture_info = resolve_id(profile_picture, avatar_data)
    avatar_picture_name = resolve_map_hash(textmap, avatar_picture_info["nameTextMapHash"])

    keyboard = None
    if show_avatars is not None and len(show_avatars) > 0:
        keyboard = Keyboard(inline=True)
        item_kbd = 0
        for avatar in show_avatars:
            avatar_show_info = resolve_id(avatar.avatar_id, avatar_data)

            item_kbd += 1
            if item_kbd > 1:
                keyboard.row()
                item_kbd = 0

            avatar_name_text = resolve_map_hash(textmap, avatar_show_info["nameTextMapHash"])
            color = Color.SECONDARY
            if avatar.level >= 90:
                color = Color.PRIMARY
            else:
                avatar_name_text += f" (Ур. {avatar.level})"

            if avatar.avatar_id == 10000046:
                color = Color.POSITIVE

            avatar_kbd_text = Callback(
                avatar_name_text,
                payload={
                    "uid": UID,
                    "avatar_id": avatar.avatar_id,
                    "avatar_name": avatar_name_text,
                },
            )

            keyboard.add(avatar_kbd_text, color)
        keyboard = keyboard.get_json()

    info_msg += f"Айди в Genshin Impact: {UID}\nНик: {nickname}\n"

    if profile_picture in FAV_AVATARS:
        info_msg += f"{avatar_picture_name} на аве, здоровья маме\n\n"
    elif avatar_picture_name is None:
        info_msg += "На аватарке никого нету (как это возможно?)"
    else:
        info_msg += f"{avatar_picture_name} на аватарке\n\n"

    info_msg += (
        f"Ранг приключений: {adv_rank}\n"
        f"Описание: {signature}\n"
        f"Уровень мира: {world_level}\n\n"
        f"Более подробная информация: https://enka.network/u/{UID}"
    )

    await message.answer(info_msg, keyboard=keyboard)


# https://api.enka.network/#/api?id=fightprop
FIGHT_PROP_NAMES = {
    "1010": 1377450402,
    "2001": 1756301290,
    "2002": 3591287138,
    "20": 1916797986,
    "22": 4137936461
}
FIGHT_PROP_DECIMAL = ("20", "22")


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    rules.PayloadMapRule([("uid", int), ("avatar_id", int), ("avatar_name", str)]),
)
async def show_avatar_info(event: MessageEvent):
    payload = event.get_payload_json()
    uid = payload['uid']
    avatar_id = payload['avatar_id']
    avatar_name = payload['avatar_name']
    try:
        player_info = await get_player_info(http_client, uid)
    except Exception as e:
        logger.error(e)
        await event.edit_message("Что-то пошло не так во время получения информации об этом персонаже")
        return

    msg = f"Информация о персонаже {avatar_name} игрока {uid}:\n"
    avatars_info = player_info.avatar_info_list
    for avatar in avatars_info:
        if avatar.avatar_id != avatar_id:
            continue
        break
    fight_prop_map = avatar.fight_prop_map
    fight_prop_map = {k for k, v in fight_prop_map.items() if v > 0}

    for k, v in fight_prop_map.items():
        if k not in FIGHT_PROP_NAMES:
            continue

        if v in FIGHT_PROP_DECIMAL:
            v = round(v, 1)
        else:
            v = int(v)

        msg += f"{FIGHT_PROP_NAMES.get(k)}: {v}\n"

    await event.edit_message(msg)
