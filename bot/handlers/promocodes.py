import time

from loguru import logger
from vkbottle.bot import BotLabeler, Message, rules

import create_pool
from item_names import PRIMOGEM
from utils import exists, gen_promocode, get_peer_id_by_exp, give_item

bl = BotLabeler()
bl.vbml_ignore_case = True


@bl.message(text="!промокод <promocode>")
async def redeem_promocode(message: Message, promocode):
    if not await exists(message):
        return
    pool = create_pool.pool
    async with pool.acquire() as pool:
        promocode_query = await pool.fetchrow(
            "SELECT * FROM promocodes WHERE promocode=$1",
            promocode
        )

        if promocode_query is None:
            return "Такого промокода не существует!"

        if promocode_query['author'] == message.from_id:
            return (
                "Пока мы живем в 2022, этот человек живет в 2032 "
                "(Вы владелец этого промокода)"
            )

        if (
            promocode_query['expire_time'] != 0
            and promocode_query['expire_time'] < int(time.time())
        ):
            return "У этого промокода истек срок!"

        if message.from_id in promocode_query['redeemed_by']:
            return "Вы уже забрали этот промокод!"

        if promocode_query['author'] != 0:
            redeemed_user_promocode = await pool.fetchrow(
                "SELECT has_redeemed_user_promocode FROM players WHERE "
                "user_id=$1 AND peer_id=$2",
                message.from_id, message.peer_id
            )

            if redeemed_user_promocode['has_redeemed_user_promocode']:
                return "Вы можете использовать только 1 промокод игрока"

            reward_author: int = await get_peer_id_by_exp(promocode_query['author'])

            if reward_author is None:
                return "Автор этого промокода - ишак, который удалил свой аккаунт из всех бесед"

            # Give 4800 primogems to the author of the promocode
            await give_item(promocode_query['author'], reward_author, PRIMOGEM, 4800)

            # Give 800 primogems to the person, who entered this promocode
            await give_item(message.from_id, message.peer_id, PRIMOGEM, 800)

            await pool.execute(
                "UPDATE players SET has_redeemed_user_promocode=true "
                "WHERE user_id=$1 AND peer_id=$2",
                message.from_id, message.peer_id
            )

            nickname_author = (await pool.fetchrow(
                "SELECT nickname FROM players WHERE user_id=$1 AND peer_id=$2",
                promocode_query['author'], reward_author
            ))['nickname']

            await message.ctx_api.messages.send(
                peer_id=reward_author,
                random_id=0,
                message=(
                    f"[id{promocode_query['author']}|{nickname_author}], "
                    f"[id{message.from_id}|этот игрок] актививировал ваш промокод, "
                    "вы получили 4800 примогемов!"
                ),
            )

            return (
                "Вы успешно активировали промокод игрока "
                f"[id{promocode_query['author']}|{nickname_author}]!\n"
                "За это вы получаете 800 примогемов"
            )

        await pool.execute(
            "UPDATE promocodes SET redeemed_by=array_append(redeemed_by, $1) WHERE promocode=$2",
            message.from_id, promocode
        )

    await give_item(
        message.from_id, message.peer_id, PRIMOGEM, promocode_query['promocode_reward']
    )

    return f"Вы успешно получили {promocode_query['promocode_reward']} примогемов!"


@bl.message(text="!мой промокод")
async def my_promocode(message: Message):
    if not await exists(message):
        return
    pool = create_pool.pool
    async with pool.acquire() as pool:
        profile_promocode = await pool.fetchrow(
            "SELECT promocode FROM promocodes WHERE author=$1",
            message.from_id
        )

        if profile_promocode is not None:
            promocode = profile_promocode['promocode']
            logger.info("using existing promocode")
        else:
            profile_promocode = await pool.fetchrow(
                "SELECT promocode FROM players WHERE user_id=$1 AND peer_id=$2",
                message.from_id, message.peer_id
            )
            if profile_promocode['promocode'] is None:
                logger.info("generating new promocode")
                promocode = await gen_promocode(800, message.from_id)
                await pool.execute(
                    "UPDATE players SET promocode=$1 WHERE user_id=$2 AND peer_id=$3",
                    promocode, message.from_id, message.peer_id
                )
            else:
                promocode = profile_promocode['promocode']

    return (
        f"Ваш промокод: \"{promocode}\"\nПоделитесь им с друзьями, что бы они "
        "могли его использовать!\nЗа каждого приглашенного человека вы получите "
        "4800 примогемов (30 круток)"
    )
