from datetime import datetime

import create_pool
import msgspec
from loguru import logger
from utils import (
    color_to_rarity,
    exists,
    get_avatar_by_name,
    get_avatar_data,
    get_textmap,
    resolve_id,
    resolve_map_hash
)
from vkbottle.bot import BotLabeler, Message

bl = BotLabeler()
bl.vbml_ignore_case = True


async def format_characters(avatars: dict, rarity: int = 5):
    """
    Avatars:
    [
        {
            "id": 1054,
            "date": 1663526623,
            "const": 0,
            "exp": 0
        },
        ...
    ]
    """
    textmap = await get_textmap()
    avatars_info = await get_avatar_data()

    new_message = f"Персонажи ({'&#11088;' * rarity}):\n"
    for avatar in avatars:
        avatar_info = resolve_id(avatar['id'], avatars_info)
        if avatar_info is None:
            logger.error(f"Unknown avatar in inventory: {avatar['id']}")
            continue

        avatar_rarity = color_to_rarity(avatar_info['qualityType'])
        if avatar_rarity != rarity:
            continue
        avatar_name = resolve_map_hash(textmap, avatar_info['nameTextMapHash'])
        avatar_consts = avatar['const']

        if avatar == avatars[-1]:
            ending = "."
        else:
            ending = ", "

        if avatar_name == "Ху Тао":
            if ending == ".":
                new_message += f"\n\n{avatar_name} (с{avatar_consts}){ending}"
            else:
                if avatar == avatars[0]:
                    new_message += f"{avatar_name} (с{avatar_consts}){ending}\n\n"
                else:
                    new_message += f"\n\n{avatar_name} (с{avatar_consts}){ending}\n\n"
        else:
            new_message += f"{avatar_name} (с{avatar_consts}){ending}"

    if new_message == f"Персонажи ({'&#11088;' * rarity}):\n":
        new_message += "Пока пусто!"
    return new_message


@bl.message(text=("!персы", "!персонажи", "!мои персонажы"))
async def list_chatacters(message: Message):
    if not await exists(message):
        return
    pool = create_pool.pool
    async with pool.acquire() as pool:
        avatars = await pool.fetchrow(
            "SELECT avatars FROM players WHERE user_id=$1 AND peer_id=$2",
            message.from_id, message.peer_id
        )

    avatars = msgspec.json.decode(avatars['avatars'].encode("utf-8"))
    if len(avatars) == 0:
        return "У вас еще нету персонажей! Их можно выбить в баннерах"

    five_stars = await format_characters(avatars)
    four_stars = await format_characters(avatars, 4)
    new_msg = f"{five_stars}\n\n{four_stars}"

    return new_msg


@bl.message(text=("!перс <avatar_name>", "!персонаж <avatar_name>"))
async def character_info(message: Message, avatar_name):
    if not await exists(message):
        return

    avatar = await get_avatar_by_name(message.from_id, message.peer_id, avatar_name)

    if avatar is None:
        return "Вы еще не выбили этого персонажа / его не существует!"

    avatar_data = await get_avatar_data()
    textmap = await get_textmap()

    avatar_excel = resolve_id(avatar['id'], avatar_data)
    avatar_name = resolve_map_hash(textmap, avatar_excel['nameTextMapHash'])
    avatar_desc = resolve_map_hash(textmap, avatar_excel['descTextMapHash'])
    avatar_rarity = color_to_rarity(avatar_excel['qualityType'])
    drop_date = avatar['date']
    const = avatar['const']

    drop_date = datetime.utcfromtimestamp(
        drop_date
    ).strftime('%H:%M:%S - %d-%m-%Y')

    new_msg = (
        f"{avatar_name} {'&#11088;' * avatar_rarity}:\n"
        f"Дата получения: {drop_date}\n"
        f"Созвездие: {const}\n"
        f"{avatar_desc}"
    )

    return new_msg
