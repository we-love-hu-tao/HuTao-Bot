from typing import Optional

from loguru import logger
from vkbottle import Callback, GroupEventType, Keyboard
from vkbottle import KeyboardButtonColor as Color
from vkbottle import ShowSnackbarEvent
from vkbottle.bot import BotLabeler, Message, MessageEvent, rules
from vkbottle.http import AiohttpClient

import create_pool
from utils import (
    get_avatar_data, get_player_info, get_textmap, resolve_id, resolve_map_hash
)
from variables import FAV_AVATARS

bl = BotLabeler()
bl.vbml_ignore_case = True

http_client = AiohttpClient()


async def generate_avatars_kbd(from_id, UID, show_avatars):
    avatar_data = await get_avatar_data()
    textmap = await get_textmap()

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
                "caller_id": from_id,
                "uid": UID,
                "avatar_id": avatar.avatar_id,
                "avatar_name": avatar_name_text,
            },
        )

        keyboard.add(avatar_kbd_text, color)
    return keyboard.get_json()


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
        keyboard = await generate_avatars_kbd(message.from_id, UID, show_avatars)

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
    '2000': 1377450402,  # HP
    '2001': 1756301290,  # ATK
    '2002': 3591287138,  # DEF
    '28': 3421163681,    # Elemental Mastery
    '20': 1916797986,    # CRIT Rate
    '22': 4137936461,    # CRIT DMG
    '26': 3911103831,    # Heal Bonus
    '23': 1735465728,    # Energy Recharge
    '30': 3763864883,    # Physical DMG Bonus
    '40': 999734248,     # Pyro DMG Bonus
    '41': 3514877774,    # Electro DMG Bonus
    '42': 3619239513,    # Hydro DMG Bonus
    '43': 1824382851,    # Dendro DMG Bonus
    '44': 312842903,     # Anemo DMG Bonus
    '45': 2557985416,    # Geo DMG Bonus
    '46': 4054347456,    # Cryo DMG Bonus
}
FIGHT_PROP_EMOJIS = {
    '2000': '💖',
    '2001': '⚔️',
    '2002': '🛡️',
    '20': '💥',
    '22': '🗡️',
    '23': '⚡',
    '26': '💊',
    '28': '🌀',
    '30': '🔥',
    '40': '🔥',
    '41': '⚡',
    '42': '💧',
    '43': '🌳',
    '44': '💨',
    '45': '🪨',
    '46': '❄️',
}
FIGHT_PROP_DECIMAL = (
    '20', '22', '23', '26', '30', '40', '41', '42', '43', '44', '45', '46'
)


@bl.raw_event(
    GroupEventType.MESSAGE_EVENT,
    MessageEvent,
    rules.PayloadMapRule([
        ("caller_id", int), ("uid", int), ("avatar_id", int), ("avatar_name", str)
    ]),
)
async def show_avatar_info(event: MessageEvent):
    payload = event.get_payload_json()
    caller_id = payload['caller_id']
    if caller_id != event.object.user_id:
        await event.ctx_api.messages.send_message_event_answer(
            event_id=event.object.event_id,
            user_id=event.object.user_id,
            peer_id=event.object.peer_id,
            event_data=ShowSnackbarEvent(
                text="Неа! Только вызывающий эту команду может увидеть билд этого персонажа"
            ).json(),
        )
        return

    uid = payload['uid']
    avatar_id = payload['avatar_id']
    avatar_name = payload['avatar_name']
    try:
        player_info = await get_player_info(http_client, uid)
    except Exception as e:
        logger.error(e)
        await event.edit_message(
            "Что-то пошло не так во время получения информации об этом персонаже"
        )
        return

    msg = f"Информация о персонаже {avatar_name} игрока {uid}:\n"
    avatars_info = player_info.avatar_info_list
    if avatars_info is None:
        await event.edit_message(
            "У этого игрока отключены подробные детали персонажей"
        )
        return
    for avatar in avatars_info:
        if avatar.avatar_id == avatar_id:
            break
    fight_prop_map = avatar.fight_prop_map
    fight_prop_map = {k: v for k, v in fight_prop_map.items() if v > 0}

    textmap = await get_textmap()
    for k, v in FIGHT_PROP_NAMES.items():
        if k not in fight_prop_map:
            continue

        fight_prop_val = fight_prop_map.get(k)
        if k in FIGHT_PROP_DECIMAL:
            fight_prop_val = round(fight_prop_val * 100, 1)
        else:
            fight_prop_val = round(fight_prop_val)

        emoji = ''
        if k in FIGHT_PROP_EMOJIS:
            emoji = FIGHT_PROP_EMOJIS[k] + ' | '

        msg += f"{emoji}{resolve_map_hash(textmap, v)}: {fight_prop_val}\n"

    # We use `copy()` since `get_player_info()` is cached, if we change
    # `show_avatar_info_list` without using `copy()`, then
    # `player_info.player_info.show_avatar_info_list` will also change
    # and will be returned every time we call `get_player_info()`
    show_avatar_info_list = player_info.player_info.show_avatar_info_list.copy()
    logger.info(show_avatar_info_list)
    for avatar in show_avatar_info_list:
        if avatar.avatar_id == avatar_id:
            show_avatar_info_list.remove(avatar)
            break

    keyboard = await generate_avatars_kbd(
        caller_id, uid, show_avatar_info_list
    )
    await event.edit_message(msg, keyboard=keyboard)
