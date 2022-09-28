from loguru import logger
from item_names import ADVENTURE_EXP, INTERTWINED_FATE
from variables import BANNERS
import re
import time
import orjson
import aiofiles
import sys
import os
import base64
import create_pool

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
    for level, exp_to_level in rank_levels_exp.items():
        if exp < exp_to_level:
            return level - 1
    return 60


textmap_cache = None
manual_textmap_cache = None
banners_cache = None
avatar_data_cache = None
weapon_data_cache = None


async def get_textmap():
    global textmap_cache
    if textmap_cache is not None:
        return textmap_cache

    async with aiofiles.open("resources/TextMapRU.json", encoding="UTF8") as file:
        textmap = await file.read()
        textmap = orjson.loads(textmap)
        textmap_cache = textmap
        return textmap


async def get_manual_textmap():
    global manual_textmap_cache
    if manual_textmap_cache is not None:
        return manual_textmap_cache

    async with aiofiles.open("resources/ManualTextMapConfigData.json", encoding="UTF8") as file:
        manual_textmap = await file.read()
        manual_textmap = orjson.loads(manual_textmap)
        manual_textmap_cache = manual_textmap
        return manual_textmap


async def get_banners():
    global banners_cache
    if banners_cache is not None:
        return banners_cache

    async with aiofiles.open("resources/Banners.json", encoding="UTF8") as file:
        banners = await file.read()
        banners = orjson.loads(banners)
        banners_cache = banners
        return banners


async def get_avatar_data():
    global avatar_data_cache
    if avatar_data_cache is not None:
        return avatar_data_cache

    async with aiofiles.open("resources/AvatarExcelConfigData.json", encoding="UTF8") as file:
        avatar_data = await file.read()
        avatar_data = orjson.loads(avatar_data)
        avatar_data_cache = avatar_data
        return avatar_data


async def get_weapon_data():
    global weapon_data_cache
    if weapon_data_cache is not None:
        return weapon_data_cache

    async with aiofiles.open("resources/WeaponExcelConfigData.json", encoding="UTF8") as file:
        weapon_data = await file.read()
        weapon_data = orjson.loads(weapon_data)
        weapon_data_cache = weapon_data
        return weapon_data


async def get_inventory(user_id: int, peer_id: int) -> list:
    pool = create_pool.pool
    async with pool.acquire() as pool:
        inventory = await pool.fetchrow(
            "SELECT inventory FROM players WHERE user_id=$1 AND peer_id=$2",
            user_id, peer_id
        )
        inventory = orjson.loads(inventory['inventory'])
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


async def get_banner_name(gacha_type) -> str:
    banner = await get_banner(gacha_type)
    title_path = banner['titlePath']

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
            f"Textmap hash doesn't exist, title_path: {title_path}"
        )
        return "Неизвестное имя баннера"

    # Remove HTML tags
    # <color=#C8A078FF>Молитва</color> новичка -> Молитва новичка
    banner_name = re.sub("(<([^>]+)>)", "", banner_name)
    return banner_name


async def get_banner(gacha_type) -> dict:
    raw_banners = await get_banners()

    for raw_banner in raw_banners:
        if raw_banner['gachaType'] == gacha_type:
            return raw_banner


async def get_banner_picture(gacha_type, prefab_path=None):
    if prefab_path is None:
        banner = await get_banner(gacha_type)
        prefab_path = banner['prefabPath'].split('_')[1]

    banner_picture = BANNERS.get(prefab_path)
    if banner_picture is None:
        # Returning fallback banner, which is standard banner
        return BANNERS.get("A022")

    return banner_picture


def give_avatar(avatars, avatar_id):
    avatar_desc = {
        "id": avatar_id,
        "date": int(time.time()),
        "const": 0,
        "exp": 0
    }
    avatars.append(avatar_desc)
    return avatars


def color_to_rarity(color_name) -> int:
    colors = {
        "QUALITY_ORANGE_SP": 5,  # Aloy rarity
        "QUALITY_ORANGE": 5,
        "QUALITY_PURPLE": 4,
        "QUALITY_BLUE": 3,
        "QUALITY_GREEN": 2,
        # There is no mention of 1* color anywhere in excel datas
    }
    return colors.get(color_name)


def check_item_type(item_id) -> int:
    if item_id >= 11101 and item_id <= 15511:
        # Weapon
        return -1

    if item_id >= 10000000 and item_id <= 11000045:
        item_id = item_id-9999000

    if item_id >= 1002 and item_id <= 1069:
        # Avatar
        return 0


def create_item(item_id, count=1):
    if item_id >= 11101 and item_id <= 20001:
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

    inventory = orjson.dumps(inventory).decode("utf-8")

    pool = create_pool.pool
    await pool.execute(
        "UPDATE players SET inventory=$1 WHERE user_id=$2 AND peer_id=$3",
        inventory, user_id, peer_id
    )


async def get_item(item_id, user_id=None, peer_id=None, inventory=None):
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
        avatars = orjson.loads(avatars['avatars'])

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
        avatars = orjson.loads(avatars['avatars'])

    avatar_data = await get_avatar_data()
    textmap = await get_textmap()
    for avatar in avatars:
        avatar_excel = resolve_id(avatar['id'], avatar_data)
        name = textmap.get(str(avatar_excel['nameTextMapHash'])).lower()
        if name == avatar_name:
            return avatar


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
                    await give_item(user_id, peer_id, INTERTWINED_FATE, new_exp)
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


def resolve_id(item_id: int, avatar_data: list = None, weapon_data: list = None) -> dict:
    item_info = None
    if avatar_data is None:
        search_in = weapon_data
    elif weapon_data is None:
        search_in = avatar_data
        if item_id <= 10000000:
            item_id += 9999000
    else:
        search_in = "both"

    if search_in != "both":
        logger.info(f"Searching {item_id} in not empty data")
        for item in search_in:
            if item['id'] == item_id:
                item_info = item
                break
    else:
        if item_id >= 11101 and item_id <= 20001:
            search_in = weapon_data
        else:
            if item_id <= 10000000:
                item_id += 9999000
            search_in = avatar_data

        for item in search_in:
            if item['id'] == item_id:
                item_info = item
                break

    return item_info


def resolve_map_hash(textmap, text_map_hash: int):
    text_map_hash = str(text_map_hash)
    return textmap.get(text_map_hash)


def get_default_header() -> dict:
    python_version = sys.version_info

    return {
        "User-Agent": (
            "Genshin-Impact-VK-Bot/{version} (Python {major}.{minor}.{micro})"
            .format(
                version=0.1,
                major=python_version.major,
                minor=python_version.minor,
                micro=python_version.micro,
            )
        )
    }
