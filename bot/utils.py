from loguru import logger
from random import randint
import time
import json
import sys
import os
import base64
import create_pool

# ! Так как формула уровней в геншине еще неизвестна,
# ! пока что у каждого уровня будет определенное
# ! количество exp
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
    # ? Уверен, что это можно было сделать лучше, сейчас
    # ? здесь вариант, сгенерированный github copilot
    for level, exp_to_level in rank_levels_exp.items():
        if exp < exp_to_level:
            return level - 1
    return 60


async def give_exp(new_exp: int, user_id: int, peer_id: int, api):
    pool = create_pool.pool
    async with pool.acquire() as pool:
        exp = await pool.fetchrow(
            "SELECT experience FROM players WHERE user_id=$1 AND peer_id=$2",
            user_id,
            peer_id,
        )
        current_exp = exp["experience"]
        current_level = exp_to_level(current_exp)
        new_level = exp_to_level(current_exp + new_exp)
        if current_level < 60:
            await pool.execute(
                "UPDATE players SET experience=experience+$1 WHERE user_id=$2"
                " AND peer_id=$3",
                new_exp,
                user_id,
                peer_id,
            )
            if current_level < new_level:
                new_rolls = None
                if new_level % 5 == 0:
                    await pool.execute(
                        "UPDATE players SET event_wishes=event_wishes+5 "
                        "WHERE user_id=$1 AND peer_id=$2",
                        user_id,
                        peer_id,
                    )
                    new_rolls = "\n+5 ивентовых молитв!"
                nickname = await pool.fetchrow(
                    "SELECT nickname FROM players WHERE user_id=$1 AND"
                    " peer_id=$2",
                    user_id,
                    peer_id,
                )
                nickname = nickname["nickname"]
                await api.messages.send(
                    peer_id=peer_id,
                    random_id=0,
                    message=(
                        f"У игрока [id{user_id}|{nickname}] повысился "
                        f"ранг приключений! Теперь он {new_level} "
                        f"{new_rolls if new_rolls is not None else ''}"
                    ),
                )

        if exp["experience"] > rank_levels_exp[60]:
            await pool.execute(
                "UPDATE players SET experience=$1 WHERE user_id=$2 AND"
                " peer_id=$3",
                rank_levels_exp[60],
                user_id,
                peer_id,
            )


async def give_primogems(amount, user_id, peer_id):
    pool = create_pool.pool
    async with pool.acquire() as pool:
        logger.info(f"Добавление пользователю {user_id} {amount} примогемов")
        await pool.execute(
            "UPDATE players SET primogems=primogems+$1 WHERE user_id=$2 AND"
            " peer_id=$3",
            amount,
            user_id,
            peer_id,
        )


# TODO: убрать characters и помещать все в inventory
# TODO: тогда можно было бы сделать все в 1 функции
async def give_character(user_id, peer_id, character_type: str, character_id):
    pool = create_pool.pool
    async with pool.acquire() as pool:
        characters = await pool.fetchrow(
            "SELECT characters FROM players WHERE user_id=$1 AND peer_id=$2",
            user_id,
            peer_id,
        )
        characters = json.loads(characters["characters"])

        for character in characters:
            if (
                character["_type"] == character_type
                and character["_id"] == character_id
            ):
                if character["const"] == 6:
                    await give_primogems(20, user_id, peer_id)
                else:
                    character["const"] += 1
                    characters = str(json.dumps(characters)).replace("'", '"')
                    await pool.execute(
                        "UPDATE players SET characters=$1::jsonb "
                        "WHERE user_id=$2 AND peer_id=$3",
                        characters,
                        user_id,
                        peer_id,
                    )
                return

        new_character = {
            "_type": character_type,
            "_id": character_id,
            "date": int(time.time()),
            "const": 0,
            "exp": 0,
            "weapon_item_id": 0,
        }
        new_character = str(new_character).replace("'", '"')

        logger.info(f"Добавление нового персонажа: {new_character}")
        await pool.execute(
            "UPDATE players SET characters=$1 || characters "
            "::jsonb WHERE user_id=$2 AND peer_id=$3",
            new_character,
            user_id,
            peer_id,
        )


async def give_weapon(user_id, peer_id, weapon_type: dict, weapon_id):
    pool = create_pool.pool
    async with pool.acquire() as pool:
        inventory = await pool.fetchrow(
            "SELECT inventory FROM players WHERE user_id=$1 AND peer_id=$2",
            user_id,
            peer_id,
        )
        inventory = json.loads(inventory["inventory"])

        for item in inventory:
            if item['item_type'] == "weapon":
                if (
                    item['weapon']['_type'] == weapon_type['_type']
                    and item['weapon']['_id'] == weapon_id
                ):
                    item["count"] += 1
                    inventory = str(json.dumps(inventory)).replace("'", '"')
                    await pool.execute(
                        "UPDATE players SET inventory=$1::jsonb "
                        "WHERE user_id=$2 AND peer_id=$3",
                        inventory,
                        user_id,
                        peer_id,
                    )
                    return

        weapon = get_drop(weapon_type, weapon_id)
        new_weapon = {
            "item_type": "weapon",
            "rarity": weapon["drop_rarity"],
            "count": 1,
            "date": int(time.time()),
            "weapon": {
                "_type": weapon_type["_type"],
                "_id": weapon_id,
                "exp": 1,
                "asc": 1,
            },
        }
        new_weapon = str(new_weapon).replace("'", '"')

        logger.info(f"Добавление нового оружия: {new_weapon}")
        await pool.execute(
            "UPDATE players SET inventory=$1 || inventory "
            "::jsonb WHERE user_id=$2 AND peer_id=$3",
            new_weapon,
            user_id,
            peer_id,
        )


def get_drop(drop_type: dict, drop_id: int) -> dict:
    for drop in drop_type.items():
        drop_name = drop[0]
        if drop_name != "_type":
            new_drop_id = drop[1]["_id"]
            if new_drop_id == drop_id:
                drop_rarity = drop[1]["rarity"]
                drop_picture = drop[1]["picture"]
                drop_name = drop[0]
                return {
                    "drop_name": drop_name,
                    "drop_id": new_drop_id,
                    "drop_rarity": drop_rarity,
                    "drop_picture": drop_picture,
                }


async def gen_promocode(reward, author_id=0, expire_time=0, custom_text=None) -> str:
    if custom_text is not None:
        promocode_text = custom_text
    else:
        token=os.urandom(9)
        promocode_text = base64.b64encode(token).decode()

    pool = create_pool.pool
    async with pool.acquire() as pool:
        await pool.execute(
            "INSERT INTO promocodes (promocode, author, expire_time, promocode_reward) "
            "VALUES ($1, $2, $3, $4)",
            promocode_text, author_id, expire_time, reward
        )

    return promocode_text


def get_default_header():
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
