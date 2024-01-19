import time

from loguru import logger
from vkbottle.bot import BotLabeler, Message

import create_pool
from item_names import PRIMOGEM
from utils import exists, gen_promo_code, get_peer_id_by_exp, give_item

bl = BotLabeler()
bl.vbml_ignore_case = True


@bl.message(text="!промокод <promocode>")
async def redeem_promo_code(message: Message, promo_code):
    if not await exists(message):
        return
    pool = create_pool.pool
    async with pool.acquire() as pool:
        promo_code_query = await pool.fetchrow(
            "SELECT * FROM promocodes WHERE promocode=$1",
            promo_code
        )

        if promo_code_query is None:
            return "Такого промокода не существует!"

        if promo_code_query['author'] == message.from_id:
            return (
                "Пока мы живем в 2024, этот человек живет в 2032 "
                "(Вы владелец этого промокода)"
            )

        if (
            promo_code_query['expire_time'] != 0
            and promo_code_query['expire_time'] < int(time.time())
        ):
            return "У этого промокода истек срок!"

        if message.from_id in promo_code_query['redeemed_by']:
            return "Вы уже забрали этот промокод!"

        if promo_code_query['author'] != 0:
            redeemed_user_promo_code = await pool.fetchrow(
                "SELECT has_redeemed_user_promocode FROM players WHERE "
                "user_id=$1 AND peer_id=$2",
                message.from_id, message.peer_id
            )

            if redeemed_user_promo_code['has_redeemed_user_promocode']:
                return "Вы можете использовать только 1 промокод игрока"

            reward_author: int = await get_peer_id_by_exp(promo_code_query['author'])

            if reward_author is None:
                return "Автор этого промокода - ишак, который удалил свой аккаунт из всех бесед"

            # Give 4800 primogems to the author of the promo code
            await give_item(promo_code_query['author'], reward_author, PRIMOGEM, 4800)

            # Give 800 primogems to the person, who entered this promo code
            await give_item(message.from_id, message.peer_id, PRIMOGEM, 800)

            await pool.execute(
                "UPDATE players SET has_redeemed_user_promocode=true "
                "WHERE user_id=$1 AND peer_id=$2",
                message.from_id, message.peer_id
            )

            nickname_author = (await pool.fetchrow(
                "SELECT nickname FROM players WHERE user_id=$1 AND peer_id=$2",
                promo_code_query['author'], reward_author
            ))['nickname']

            await message.ctx_api.messages.send(
                peer_id=reward_author,
                random_id=0,
                message=(
                    f"[id{promo_code_query['author']}|{nickname_author}], "
                    f"[id{message.from_id}|этот игрок] актививировал ваш промокод, "
                    "вы получили 4800 примогемов!"
                ),
            )

            return (
                "Вы успешно активировали промокод игрока "
                f"[id{promo_code_query['author']}|{nickname_author}]!\n"
                "За это вы получаете 800 примогемов"
            )

        await pool.execute(
            "UPDATE promocodes SET redeemed_by=array_append(redeemed_by, $1) WHERE promocode=$2",
            message.from_id, promo_code
        )

    await give_item(
        message.from_id, message.peer_id, PRIMOGEM, promo_code_query['promocode_reward']
    )

    return f"Вы успешно получили {promo_code_query['promocode_reward']} примогемов!"


@bl.message(text="!мой промокод")
async def my_promo_code(message: Message):
    if not await exists(message):
        return
    pool = create_pool.pool
    async with pool.acquire() as pool:
        profile_promo_code = await pool.fetchrow(
            "SELECT promocode FROM promocodes WHERE author=$1",
            message.from_id
        )

        if profile_promo_code is not None:
            promo_code = profile_promo_code['promocode']
            logger.info("using existing promocode")
        else:
            profile_promo_code = await pool.fetchrow(
                "SELECT promocode FROM players WHERE user_id=$1 AND peer_id=$2",
                message.from_id, message.peer_id
            )
            if profile_promo_code['promocode'] is None:
                logger.info("Generating new promo code")
                promo_code = await gen_promo_code(800, message.from_id)
                await pool.execute(
                    "UPDATE players SET promocode=$1 WHERE user_id=$2 AND peer_id=$3",
                    promo_code, message.from_id, message.peer_id
                )
            else:
                promo_code = profile_promo_code['promocode']

    return (
        f"Ваш промокод: \"{promo_code}\"\nПоделитесь им с друзьями, что бы они "
        "могли его использовать!\nЗа каждого приглашенного человека вы получите "
        "4800 примогемов (30 круток)"
    )
