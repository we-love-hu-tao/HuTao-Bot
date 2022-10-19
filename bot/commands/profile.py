import msgspec
from loguru import logger
from vkbottle.bot import Blueprint, Message
from vkbottle.http import AiohttpClient

import create_pool
from item_names import ACQUAINT_FATE, ADVENTURE_EXP, INTERTWINED_FATE, PRIMOGEM
from utils import (exists, exp_to_level, get_avatar_data, get_item,
                   get_player_info, get_textmap, resolve_id, resolve_map_hash)

bp = Blueprint("Profile")
bp.labeler.vbml_ignore_case = True


@bp.on.chat_message(text=(
    '!персонаж', '!перс', '!gthc',
    '!пероснаж', '!прес', '!епрс',
    '!пнрс', '!пнерс', '!поес'
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
            "gacha_info "
            "FROM players WHERE user_id=$1 and peer_id=$2",
            message.from_id, message.peer_id
        )

    nickname = result['nickname']
    UID = result['uid']

    gacha_info = msgspec.json.decode(result['gacha_info'])
    if len(gacha_info) > 0:
        event_pity5 = gacha_info['eventCharacterBanner']['pity5']
    else:
        event_pity5 = 0

    experience = await get_item(ADVENTURE_EXP, message.from_id, message.peer_id)
    experience = experience['count']
    level = exp_to_level(experience)

    primogems = await get_item(PRIMOGEM, message.from_id, message.peer_id)
    primogems = primogems['count']

    standard_wishes = await get_item(ACQUAINT_FATE, message.from_id, message.peer_id)
    standard_wishes = standard_wishes['count']

    event_wishes = await get_item(INTERTWINED_FATE, message.from_id, message.peer_id)
    event_wishes = event_wishes['count']

    return (
        f"&#128100; | Ник: {nickname}\n"
        f"&#128200; | Уровень: {level}\n"
        f"&#128160; | Примогемы: {primogems}\n"
        f"&#128311; | Стандартных молитв: {standard_wishes}\n"
        f"&#128310; | Молитв события: {event_wishes}\n\n"

        f"&#10133; | Гарант в ивентовых баннерах: {event_pity5}\n\n"

        f"&#128100; | Айди в Genshin Impact: {UID if UID else 'не установлен!'}"
    )


@bp.on.chat_message(text=("!баланс", "!крутки", "!примогемы"))
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


FAV_AVATARS = (
    10000046,  # Hu Tao
    10000042,  # Keqing
    10000021,  # Amber
    10000049,  # Yoimiya
    10000054,  # Kokomi
    10000073,  # Nahida
)


@bp.on.chat_message(text=("!геншин инфо", "!геншин инфо <UID:int>"))
async def genshin_info(message: Message, UID: int = None):
    if not await exists(message):
        return

    info_msg = ""

    if UID is None:
        pool = create_pool.pool
        async with pool.acquire() as pool:
            if message.reply_message is None:
                UID = await pool.fetchrow(
                    "SELECT uid FROM players WHERE user_id=$1 AND peer_id=$2",
                    message.from_id, message.peer_id
                )

                if UID['uid'] is None:
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
    profile_picture = player_info.profile_picture.avatar_id

    avatar_data = await get_avatar_data()
    textmap = await get_textmap()
    avatar_picture_info = resolve_id(profile_picture, avatar_data)
    avatar_picture_name = resolve_map_hash(textmap, avatar_picture_info['nameTextMapHash'])

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

    return info_msg
