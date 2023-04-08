import base64
import os
import re
import sys
import time

import aiofiles
import msgspec
from aiocache import cached
from loguru import logger
from vkbottle import API
from vkbottle.bot import Message
from vkbottle.http import AiohttpClient

import create_pool
from config import CURRENT_LANG
from item_names import ADVENTURE_EXP, INTERTWINED_FATE
from keyboards import KEYBOARD_START
from models.banner import Banner
from models.player_profile import PlayerProfile

rank_levels_exp = {
    1: 0,
    2: 375,
    3: 875,
    4: 1500,
    5: 2225,
    6: 3075,
    7: 4025,
    8: 5100,
    9: 6275,
    10: 7575,
    11: 9000,
    12: 10525,
    13: 12175,
    14: 13950,
    15: 15825,
    16: 17825,
    17: 20200,
    18: 22700,
    19: 25325,
    20: 28100,
    21: 30925,
    22: 34350,
    23: 38075,
    24: 42075,
    25: 46375,
    26: 50950,
    27: 55825,
    28: 60975,
    29: 66425,
    30: 72150,
    31: 78175,
    32: 84475,
    33: 91075,
    34: 97975,
    35: 105150,
    36: 112625,
    37: 120375,
    38: 128425,
    39: 136750,
    40: 145375,
    41: 155925,
    42: 167450,
    43: 179925,
    44: 193375,
    45: 207775,
    46: 223125,
    47: 239450,
    48: 256725,
    49: 274975,
    50: 294175,
    51: 320575,
    52: 349375,
    53: 380575,
    54: 414175,
    55: 450175,
    56: 682525,
    57: 941475,
    58: 1227225,
    59: 1540050,
    60: 1880175,
}


def exp_to_level(exp: int):
    for level, level_exp in rank_levels_exp.items():
        if exp < level_exp:
            return level - 1
    return 60


def level_to_exp(level: int):
    return rank_levels_exp.get(level) or rank_levels_exp[60]


def count_quests_time(exp):
    """
    Based on player level, players will have different quest time
    """
    player_level = exp_to_level(exp)
    if player_level == 60:
        quest_time = 60
    elif player_level > 45:
        quest_time = 240
    elif player_level > 35:
        quest_time = 420
    elif player_level > 20:
        quest_time = 600
    elif player_level > 10:
        quest_time = 900
    else:
        quest_time = 1200

    return quest_time


@cached(key="textmap")
async def get_textmap():
    logger.info("Loading textmap data...")
    async with aiofiles.open(
        "resources/TextMapRU.json", mode='rb'
    ) as file:
        textmap = await file.read()
        textmap = msgspec.json.decode(textmap)
        return textmap


@cached(key="manual_textmap")
async def get_manual_textmap():
    logger.info("Loading manual textmap data...")
    async with aiofiles.open(
        "resources/ManualTextMapConfigData.json", mode='rb'
    ) as file:
        manual_textmap = await file.read()
        manual_textmap = msgspec.json.decode(manual_textmap)
        return manual_textmap


@cached(key="banners")
async def get_banners():
    logger.info("Loading banner data...")
    async with aiofiles.open(
        "resources/Banners.json", mode='rb'
    ) as file:
        banners_raw = await file.read()
        banners = msgspec.json.decode(banners_raw)
        return tuple(banners)


@cached(key="avatar_data")
async def get_avatar_data():
    logger.info("Loading avatar data...")
    async with aiofiles.open(
        "resources/AvatarExcelConfigData.json", mode='rb'
    ) as file:
        avatar_data = await file.read()
        avatar_data = msgspec.json.decode(avatar_data)
        return avatar_data


@cached(key="skill_depot_data")
async def get_skill_depot_data():
    logger.info("Loading skill depot data...")
    async with aiofiles.open(
        "resources/AvatarSkillDepotExcelConfigData.json", mode='rb'
    ) as file:
        skill_depot_data = await file.read()
        skill_depot_data = msgspec.json.decode(skill_depot_data)
        return tuple(skill_depot_data)


@cached(key="skill_excel_data")
async def get_skill_excel_data():
    logger.info("Loading skill excel data...")
    async with aiofiles.open(
        "resources/AvatarSkillExcelConfigData.json", mode='rb'
    ) as file:
        skill_data = await file.read()
        skill_data = msgspec.json.decode(skill_data)
        return tuple(skill_data)


@cached(key="weapon_data")
async def get_weapon_data():
    logger.info("Loading weapon data...")
    async with aiofiles.open(
        "resources/WeaponExcelConfigData.json", mode='rb'
    ) as file:
        weapon_data = await file.read()
        weapon_data = msgspec.json.decode(weapon_data)
        return tuple(weapon_data)


@cached(key="language_bot")
async def get_language_file(language):
    file_exists = os.path.exists(f"languages/{language}.json")
    if not file_exists:
        logger.warning(f"Language file {language}.json doesn't exists, fallback to ru.json")
        language = "ru"

    async with aiofiles.open(
        f"languages/{language}.json", mode='rb'
    ) as file:
        content = await file.read()
    return msgspec.json.decode(content)


async def translate(category: str, value: str, language: str | None = None):
    language = language or CURRENT_LANG

    language_file = await get_language_file(language)
    fallback_language_file = {}
    if language != "ru":
        fallback_language_file = await get_language_file("ru")

    using_fallback = False
    if language_file.get(category) is None:
        if fallback_language_file.get(category) is None:
            raise ValueError(f"Wrong language category: {category}")
        else:
            using_fallback = True

    if using_fallback:
        if fallback_language_file[category].get(value) is None:
            raise ValueError(f"Wrong translate value (in fallback): {value}")

    else:
        if language_file[category].get(value) is None:
            if fallback_language_file[category].get(value) is None:
                raise ValueError(f"Wrong translate value: {value}")
            else:
                return fallback_language_file[category][value]
        else:
            return language_file[category][value]


async def get_inventory(user_id: int, peer_id: int) -> list:
    pool = create_pool.pool
    async with pool.acquire() as pool:
        inventory = await pool.fetchrow(
            "SELECT inventory FROM players WHERE user_id=$1 AND peer_id=$2",
            user_id, peer_id
        )
        inventory = msgspec.json.decode(inventory['inventory'].encode("utf-8"))
        return inventory


async def get_peer_id_by_exp(user_id) -> int:
    pool = create_pool.pool
    async with pool.acquire() as pool:
        player_accounts = await pool.fetch(
            "SELECT peer_id FROM players WHERE user_id=$1",
            user_id
        )

    most_exp = 0
    peer_id = 0
    for account in player_accounts:
        exp = await get_item(ADVENTURE_EXP, user_id, account['peer_id'])
        if exp['count'] > most_exp:
            most_exp = exp['count']
            peer_id = account['peer_id']

    return peer_id


async def get_banner_name(gacha_type, add_main=False) -> str:
    banner = await get_banner(gacha_type)
    if banner is None:
        return "Несуществующий баннер"

    title_path = banner.title_path

    textmap = await get_textmap()
    raw_banner_names = await get_manual_textmap()

    name_id = None
    for item in raw_banner_names:
        if item['textMapId'] == title_path:
            name_id = item['textMapContentTextMapHash']
            break

    if name_id is None:
        logger.warning(f"Unknown title path passed: {title_path}")
        return "Неизвестный баннер"

    banner_name = resolve_map_hash(textmap, name_id)
    if banner_name is None:
        logger.warning(
            f"Textmap hash {name_id} doesn't exist, title_path: {title_path}"
        )
        return "Неизвестное имя баннера"

    # Remove HTML tags
    # <color=#C8A078FF>Молитва</color> новичка -> Молитва новичка
    banner_name = re.sub("(<([^>]+)>)", "", banner_name)

    if add_main:
        main_rateup = None
        if len(banner.rate_up_items_5) > 0:
            main_rateup = banner.rate_up_items_5[0]
        elif len(banner.rate_up_items_4) > 0:
            main_rateup = banner.rate_up_items_4[0]
        if main_rateup is None:
            return banner_name

        avatar_data = await get_avatar_data()
        weapon_data = await get_weapon_data()
        item_data = resolve_id(main_rateup, avatar_data, weapon_data)
        if item_data is None:
            logger.warning(f"Couldn't resolve item {main_rateup}")
        else:
            item_name = resolve_map_hash(textmap, item_data['nameTextMapHash'])
            banner_name += f' ({item_name})'

    return banner_name


async def get_banner(gacha_type) -> Banner | None:
    """Returns banner from `Banners.json`, converted into a `Banner` object"""
    raw_banners = await get_banners()

    for raw_banner in raw_banners:
        if raw_banner['gachaType'] == gacha_type:
            return msgspec.json.decode(msgspec.json.encode(raw_banner), type=Banner)


def give_avatar(avatars, avatar_id):
    avatar_desc = {
        "id": avatar_id,
        "date": int(time.time()),
        "const": 0,
        "exp": 0
    }
    avatars.append(avatar_desc)
    return avatars


async def exists(event: Message, pool=None) -> bool:
    """Checks, if player is registered in bot"""

    is_banned_request = "SELECT user_id FROM banned WHERE user_id=$1"
    exists_request = "SELECT user_id FROM players WHERE user_id=$1 AND peer_id=$2"

    if pool is not None:
        is_banned = await pool.fetchrow(is_banned_request, event.from_id)
        row = await pool.fetchrow(exists_request, event.from_id, event.peer_id)
    else:
        pool = create_pool.pool
        async with pool.acquire() as pool:
            is_banned = await pool.fetchrow(is_banned_request, event.from_id)
            row = await pool.fetchrow(exists_request, event.from_id, event.peer_id)

    if is_banned is None:    # If user isn't banned
        if row is not None:  # If user exists
            return True
        else:
            await event.answer(
                "Для начала нужно зайти в Genshin Impact командой !начать",
                keyboard=KEYBOARD_START
            )
    else:
        await event.answer("нет (разбан у [id322615766|меня]).", disable_mentions=True)

    return False


def color_to_rarity(color_name) -> int | None:
    colors = {
        "QUALITY_ORANGE_SP": 5,  # Aloy rarity
        "QUALITY_ORANGE": 5,
        "QUALITY_PURPLE": 4,
        "QUALITY_BLUE": 3,
        "QUALITY_GREEN": 2,
        # There is no mention of 1* color anywhere in excel datas
    }
    return colors.get(color_name)


def element_to_banner_bg(element_name):
    elements = {
        "electric": "Elect",
        "fire": "Fire",
        "grass": "Grass",
        "ice": "Ice",
        "rock": "Rock",
        "water": "Water",
        "wind": "Wind",
    }
    return elements.get(element_name.lower())


def check_item_type(item_id) -> int | None:
    if 11101 <= item_id <= 15511:
        # Weapon
        return -1

    if 10000000 <= item_id <= 11000100:
        item_id = item_id-9999000

    if 1002 <= item_id <= 1100:
        # Avatar
        return 0


def create_item(item_id, count=1):
    if 11101 <= item_id <= 20001:
        item_type = "ITEM_WEAPON"
    else:
        item_type = "ITEM_OTHER"
    item_desc = {
        "item_type": item_type,
        "id": item_id,
        "date": int(time.time()),
        "count": count
    }
    return item_desc


def give_item_local(inventory, item_id, count=1):
    for item in inventory:
        if item['id'] == item_id:
            logger.info(f"Found {item['id']}")
            item['count'] += count
            return inventory

    item_desc = create_item(item_id, count)
    inventory.append(item_desc)

    return inventory


async def give_item(user_id: int, peer_id: int, item_id: int, count: int = 1, give_or_set="give"):
    inventory = await get_inventory(user_id, peer_id)

    has_item = False
    for item in inventory:
        if item['id'] == item_id:
            logger.info(f"Found {item['id']}")
            has_item = True
            if give_or_set == "give":
                item['count'] += count
            else:
                item['count'] = count
            logger.info(f"Inventory after updating: {inventory}")
            break

    if count > 0:
        if not has_item:
            item_desc = create_item(item_id, count)
            inventory.append(item_desc)

    inventory = msgspec.json.encode(inventory).decode("utf-8")

    pool = create_pool.pool
    await pool.execute(
        "UPDATE players SET inventory=$1 WHERE user_id=$2 AND peer_id=$3",
        inventory, user_id, peer_id
    )


async def get_item(
    item_id: int,
    user_id: int = 0,
    peer_id: int = 0,
    inventory: list[dict] | None = None
):
    if inventory is None:
        inventory = await get_inventory(user_id, peer_id)

    for item in inventory:
        if item['id'] == item_id:
            return item

    return create_item(item_id, 0)


async def get_avatar(user_id, peer_id, avatar_id):
    pool = create_pool.pool
    async with pool.acquire() as pool:
        avatars = await pool.fetchrow(
            "SELECT avatars FROM players WHERE user_id=$1 AND peer_id=$2",
            user_id, peer_id,
        )
        avatars = msgspec.json.decode(avatars['avatars'].encode("utf-8"))

    for avatar in avatars:
        if avatar['id'] == avatar_id:
            return avatar


async def get_avatar_by_name(user_id, peer_id, avatar_name):
    avatar_name = avatar_name.lower()
    pool = create_pool.pool
    async with pool.acquire() as pool:
        avatars = await pool.fetchrow(
            "SELECT avatars FROM players WHERE user_id=$1 AND peer_id=$2",
            user_id, peer_id,
        )
        avatars = msgspec.json.decode(avatars['avatars'].encode("utf-8"))

    avatar_data = await get_avatar_data()
    textmap = await get_textmap()
    for avatar in avatars:
        avatar_excel = resolve_id(avatar['id'], avatar_data)

        if avatar_excel is not None:
            name = textmap.get(str(avatar_excel['nameTextMapHash'])).lower()
            if name == avatar_name:
                return avatar
        else:
            logger.warning(f"Couldn't read avatar {avatar['id']} while getting it's name")


async def give_exp(new_exp: int, user_id: int, peer_id: int, api):
    pool = create_pool.pool
    async with pool.acquire() as pool:
        current_exp = await get_item(ADVENTURE_EXP, user_id, peer_id)
        current_level = exp_to_level(current_exp['count'])
        new_level = exp_to_level(current_exp['count'] + new_exp)
        if current_level < 60:
            await give_item(user_id, peer_id, ADVENTURE_EXP, new_exp)
            if current_level < new_level:
                new_rolls = None
                if new_level % 5 == 0:
                    await give_item(user_id, peer_id, INTERTWINED_FATE, 5)
                    new_rolls = "\n+5 ивентовых молитв!"
                nickname = await pool.fetchrow(
                    "SELECT nickname FROM players WHERE user_id=$1 AND "
                    "peer_id=$2",
                    user_id,
                    peer_id,
                )
                nickname = nickname['nickname']
                await api.messages.send(
                    peer_id=peer_id,
                    random_id=0,
                    message=(
                        f"У игрока [id{user_id}|{nickname}] повысился "
                        f"ранг приключений! Теперь он {new_level} "
                        f"{new_rolls if new_rolls is not None else ''}"
                    ),
                )

        if current_exp['count'] > rank_levels_exp[60]:
            await give_item(user_id, peer_id, ADVENTURE_EXP, rank_levels_exp[60], "set")


async def gen_promocode(reward, author_id=0, expire_time=0, custom_text=None) -> str:
    """
    Generates promocode.
    This may be either player promocode, or original promocode
    """
    if custom_text is not None:
        promocode_text = custom_text
    else:
        token = os.urandom(9)
        promocode_text = base64.b64encode(token).decode("utf-8")

    pool = create_pool.pool
    async with pool.acquire() as pool:
        await pool.execute(
            "INSERT INTO promocodes (promocode, author, expire_time, promocode_reward) "
            "VALUES ($1, $2, $3, $4)",
            promocode_text, author_id, expire_time, reward
        )

    return promocode_text


def resolve_id(
    item_id: int,
    avatar_data: list | None = None,
    weapon_data: list | None = None
) -> dict | None:
    if not avatar_data and not weapon_data:
        raise ValueError("No data to resolve id provided")

    if 11101 <= item_id <= 20001:
        search_in = weapon_data
        searched_in = "weapon data"
    else:
        if item_id <= 10000000:
            item_id += 9999000
        search_in = avatar_data
        searched_in = "avatar data"

    item_info = None

    logger.info(f"Searching {item_id} in {searched_in}")
    for item in search_in:
        if item['id'] == item_id:
            item_info = item
            break

    if item_info is None:
        logger.warning(f"Couldn't find item with id {item_id}, searched in {searched_in}")
    return item_info


def resolve_map_hash(textmap: dict, text_map_hash: int | str) -> str | None:
    """Gets a string from a text map hash"""
    text_map_hash = str(text_map_hash)
    return textmap.get(text_map_hash)


async def report_error(api: API, error: Exception):
    # TODO: report errors in group dms
    pass


@cached(ttl=60)
async def get_player_info(
        http_client: AiohttpClient, uid: int, only_info: bool = False
) -> PlayerProfile | None:
    """
    Gets account information from enka.network and
    converts it into an `PlayerProfile` object
    """
    player_info = await http_client.request_content(
        f"https://enka.network/api/uid/{uid}{'?info' if only_info else ''}",
        headers=get_default_header()
    )
    try:
        player_info = msgspec.json.decode(player_info, type=PlayerProfile)
    except msgspec.ValidationError as e:
        logger.error(f"Error while trying to validate enka.network response: {e}")
        player_info = None

    return player_info


def get_default_header() -> dict:
    python_version = sys.version_info
    version = 1.0
    major = python_version.major
    minor = python_version.minor
    micro = python_version.micro

    return {
        "User-Agent": f"HuTao-Bot/{version} (Python {major}.{minor}.{micro})"
    }
