import time

import msgspec
from loguru import logger
from vkbottle import Callback, Keyboard, Text
from vkbottle import KeyboardButtonColor as Color
from vkbottle.bot import BotLabeler, Message, rules
from vkbottle.http import AiohttpClient
from typing import Optional

import create_pool
from item_names import ACQUAINT_FATE, ADVENTURE_EXP, INTERTWINED_FATE, PRIMOGEM
from utils import (count_quests_time, exists, exp_to_level, get_avatar_data, get_item,
                   get_player_info, get_textmap, resolve_id, resolve_map_hash)
from variables import FAV_AVATARS

bl = BotLabeler()
bl.vbml_ignore_case = True

http_client = AiohttpClient()


@bl.message(text=(
    '!персонаж', '!перс', '!gthc', '! перс',
    '[<!>|<!>] Персонаж', 'Персонаж',
))
async def profile(message: Message):
    if not await exists(message):
        return
    pool = create_pool.pool
    async with pool.acquire() as pool:
        result = await pool.fetchrow(
            "SELECT "
            "nickname, "
            "uid, "
            "gacha_info, "
            "reward_last_time, "
            "daily_quests_time, "
            "doing_quest "
            "FROM players WHERE user_id=$1 and peer_id=$2",
            message.from_id, message.peer_id
        )

    nickname = result['nickname']
    UID = result['uid']

    gacha_info = msgspec.json.decode(result['gacha_info'].encode("utf-8"))
    if len(gacha_info) > 0:
        event_pity5 = gacha_info['eventCharacterBanner']['pity5']
    else:
        event_pity5 = 0

    reward_last_time = result['reward_last_time']
    started_time = result['daily_quests_time']
    doing_quest = result['doing_quest']

    experience = await get_item(ADVENTURE_EXP, message.from_id, message.peer_id)
    experience = experience['count']
    level = exp_to_level(experience)
    quest_time = count_quests_time(experience)

    primogems = await get_item(PRIMOGEM, message.from_id, message.peer_id)
    primogems = primogems['count']

    standard_wishes = await get_item(ACQUAINT_FATE, message.from_id, message.peer_id)
    standard_wishes = standard_wishes['count']

    event_wishes = await get_item(INTERTWINED_FATE, message.from_id, message.peer_id)
    event_wishes = event_wishes['count']

    keyboard = Keyboard(inline=True)
    if int(time.time()) > reward_last_time + 86400:
        keyboard.add(Text("Награда"), color=Color.POSITIVE)

    if started_time + 86400 < int(time.time()) and doing_quest is False:
        keyboard.add(Text("Начать поручения"))

    if started_time + quest_time < int(time.time()) and doing_quest:
        keyboard.add(Text("Завершить поручения"), color=Color.POSITIVE)

    await message.answer(
        f"&#128100; | Ник: {nickname}\n"
        f"&#128200; | Уровень: {level}\n"
        f"&#128160; | Примогемы: {primogems}\n"
        f"&#128311; | Стандартных молитв: {standard_wishes}\n"
        f"&#128310; | Молитв события: {event_wishes}\n\n"

        f"&#10133; | Гарант в ивентовых баннерах: {event_pity5}\n\n"

        f"&#128100; | Айди в Genshin Impact: {UID if UID else 'не установлен!'}",
        keyboard=keyboard.get_json()
    )


@bl.message(text=(
    '!баланс', '!крутки', '!примогемы', '! баланс'
))
async def check_balance(message: Message):
    if not await exists(message):
        return

    primogems = await get_item(PRIMOGEM, message.from_id, message.peer_id)
    primogems = primogems['count']

    event_wishes = await get_item(INTERTWINED_FATE, message.from_id, message.peer_id)
    event_wishes = event_wishes['count']
    standard_wishes = await get_item(ACQUAINT_FATE, message.from_id, message.peer_id)
    standard_wishes = standard_wishes['count']

    return (
        f"&#128160; | Примогемы: {primogems}\n"
        f"&#128160; | Ивентовые крутки: {event_wishes}\n"
        f"&#128160; | Стандартные крутки: {standard_wishes}"
    )


@bl.message(text=(
    "!геншин инфо", "!геншин инфо <UID:int>",
    "! геншин инфо", " ! геншин инфо <UID:int>"
))
async def genshin_info(message: Message, UID: Optional[int] = None):
    info_msg = ""

    if UID is None:
        pool = create_pool.pool
        async with pool.acquire() as pool:
            if message.reply_message is None:
                UID = await pool.fetchrow(
                    "SELECT uid FROM players WHERE user_id=$1 AND peer_id=$2",
                    message.from_id, message.peer_id
                )

                if UID is None or UID['uid'] is None:
                    return (
                        "Вы не установили свой UID! "
                        "Его можно установить с помощью команды \"!установить айди <UID>\""
                    )
            else:
                UID = await pool.fetchrow(
                    "SELECT uid FROM players WHERE user_id=$1 AND peer_id=$2",
                    message.reply_message.from_id, message.peer_id
                )

                if UID is None or UID['uid'] is None:
                    return (
                        "Человек, на которого вы ответили, еще не создал аккаунт "
                        "/ не указал айди, однако он может это сделать, написав "
                        "\"!установить айди <UID>\""
                    )
                info_msg += (
                    f"Информация об аккаунте [id{message.reply_message.from_id}|этого] игрока\n\n"
                )

            UID = UID['uid']

    try:
        player_info = await get_player_info(http_client, UID)
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
    avatar_picture_name = resolve_map_hash(textmap, avatar_picture_info['nameTextMapHash'])

    keyboard = None
    if show_avatars is not None and len(show_avatars) > 0:
        keyboard = Keyboard(inline=True)
        item_kbd = 0
        for avatar in show_avatars:
            avatar_show_info = resolve_id(avatar.avatar_id, avatar_data)
            avatar_show_name = resolve_map_hash(textmap, avatar_show_info['nameTextMapHash']) 

            item_kbd += 1
            if item_kbd > 1:
                keyboard.row()
                item_kbd = 0

            avatar_name_text = avatar_show_name
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
                    "avatar_id": avatar.avatar_id
            })

            keyboard.add(avatar_kbd_text, color)
        keyboard = keyboard.get_json()

    info_msg += (
        f"Айди в Genshin Impact: {UID}\n"
        f"Ник: {nickname}\n"
    )

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
