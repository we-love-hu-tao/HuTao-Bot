import subprocess
import time
from typing import Optional

from loguru import logger
from vkbottle import VKAPIError
from vkbottle.bot import BotLabeler, Message
from vkbottle.dispatch.rules import ABCRule

import create_pool
from item_names import PRIMOGEM
from utils import (
    gen_promocode, give_exp, give_item, get_achvmt, give_achvmt
)


class AdminRule(ABCRule[Message]):
    """Rule which checks, if user id is admin"""
    async def check(self, event: Message) -> bool:
        return event.from_id in admin_list


bl = BotLabeler()
bl.auto_rules = [AdminRule()] 
bl.vbml_ignore_case = True

admin_list = (322615766, 328328155)

@bl.message(text=("!гнш беседы <mention>", "!гнш беседы"))
async def list_user_chat(message: Message, mention=None):
    if mention is not None:
        mention_id = int(mention.split("|")[0][1:].replace("id", ""))
    else:
        if message.reply_message is not None:
            mention_id = message.reply_message.from_id
        else:
            mention_id = message.from_id

    pool = create_pool.pool
    async with pool.acquire() as pool:
        raw_chats = await pool.fetch(
            "SELECT peer_id FROM players WHERE user_id=$1", mention_id
        )

    if len(raw_chats) == 0:
        await message.answer(
            f"У [id{mention_id}|этого] пользователя нету аккаунтов в боте",
            disable_mentions=True
        )
        return

    to_send = f"Айди бесед [id{mention_id}|этого] пользователя:\n"
    for chat in raw_chats:
        if chat['peer_id'] == message.from_id:
            to_send += "ЛС"
        else:
            to_send += f"{chat['peer_id']}"

        if chat['peer_id'] == message.peer_id:
            to_send += " - эта беседа"
        to_send += "\n"

    await message.answer(to_send, disable_mentions=True)


@bl.message(text=(
    "+примогемы <amount:int>",
    "+примогемы <amount>",
    "+примогемы <amount:int> <mention> <peer_id:int>",
))
async def give_primogems(
    message: Message,
    amount: int | str,
    mention: Optional[str] = None,
    peer_id: Optional[int] = None
):
    try:
        amount = int(amount)
    except ValueError:
        return "Количество примогемов должно быть числом!"

    if mention is None:
        if message.reply_message is None:
            mention_id = message.from_id
        else:
            mention_id = message.reply_message.from_id
    else:
        mention_id = int(mention.split("|")[0][1:].replace("id", ""))

    if peer_id is None:
        peer_id = message.peer_id
    else:
        if peer_id < 2000000000:
            peer_id += 2000000000

    pool = create_pool.pool
    async with pool.acquire() as pool:
        is_exists = await pool.fetchrow(
            "SELECT user_id FROM players WHERE user_id=$1 AND peer_id=$2",
            mention_id, peer_id
        )
        if is_exists is not None:
            logger.info(f"Добавление пользователю {mention_id} {amount} примогемов")

            await give_item(mention_id, peer_id, PRIMOGEM, amount)

            return f"[id{mention_id}|Этому пользователю] было добавлено {amount} примогемов"
        else:
            return "Такого пользователя нет в игре!"


@bl.message(text=(
    "+уровень <amount:int>",
    "+уровень <amount:int> <mention> <peer_id:int>"
))
async def give_level(
    message: Message,
    amount: int,
    mention: Optional[str] = None,
    peer_id: Optional[int] = None
):
    if mention is None:
        if message.reply_message is None:
            mention_id = message.from_id
        else:
            mention_id = message.reply_message.from_id
    else:
        mention_id = int(mention.split("|")[0][1:].replace("id", ""))

    if peer_id is None:
        peer_id = message.peer_id
    else:
        if peer_id < 2000000000:
            peer_id += 2000000000

    pool = create_pool.pool
    async with pool.acquire() as pool:
        is_exists = await pool.fetchrow(
            "SELECT user_id FROM players WHERE user_id=$1 AND peer_id=$2",
            mention_id, peer_id
        )
        if is_exists is not None:
            logger.info(f"Добавление пользователю {mention_id} {amount} опыта")

            await give_exp(amount, mention_id, peer_id, message.ctx_api)

            return f"[id{mention_id}|Этому пользователю] было добавлено {amount} опыта!"
        else:
            return "Такого пользователя нет в игре!"


@bl.message(text=("!гнш бан <mention>", "!гнш бан"))
async def ban_user(message: Message, mention=None):
    if mention is not None:
        mention_id = int(mention.split("|")[0][1:].replace("id", ""))
    else:
        if message.reply_message is not None:
            mention_id = message.reply_message.from_id
        else:
            await message.answer("так ответь на сообщение")
    pool = create_pool.pool
    async with pool.acquire() as pool:
        is_exists = await pool.fetchrow(
            "SELECT user_id FROM banned WHERE user_id=$1",
            mention_id
        )
        if is_exists is None:
            logger.info(f"Бан пользователя {mention_id}")
            await pool.execute(
                "INSERT INTO banned (user_id) VALUES ($1)",
                mention_id,
            )
            await message.answer(
                "этот человек совершил что-то ужасное, поэтому был забанен"
            )
        else:
            await message.answer("этот человек уже забанен")
    try:
        await message.ctx_api.messages.remove_chat_user(
            chat_id=message.chat_id, user_id=mention_id
        )
    except ValueError as e:
        logger.info(f"Couldn't ban user from chat: {e}")


@bl.message(text=("!гнш разбан <mention>", "!гнш разбан"))
async def unban_user(message: Message, mention=None):
    if mention is not None:
        mention_id = int(mention.split("|")[0][1:].replace("id", ""))
    else:
        if message.reply_message is not None:
            mention_id = message.reply_message.from_id
        else:
            await message.answer("так ответь на сообщение")
    pool = create_pool.pool
    async with pool.acquire() as pool:
        is_exists = await pool.fetchrow(
            "SELECT user_id FROM banned WHERE user_id=$1",
            mention_id
        )
        if is_exists is not None:
            logger.info(f"Разбан пользователя {mention_id}")
            await pool.execute(
                "DELETE FROM banned WHERE user_id=$1",
                mention_id,
            )
            await message.answer(
                "этот человек снова стал крутым, поэтому был разбанен"
            )
        else:
            await message.answer("этот человек, к счастью не забанен")


@bl.message(
    text=(
        "!новый промокод <!>",
        "!новый промокод"
    )
)
async def create_new_promocode(message: Message):
    if len(message.text.split()) == 2:
        return "!новый промокод <количество> <время (unix time)> <название>"

    try:
        msg_params = message.text.split()[2:]
        amount = int(msg_params[0])
        expire_time = int(msg_params[1])
        custom_text = msg_params[2]

        if expire_time < int(time.time()) and expire_time != 0:
            return "Некорректное время!"

        new_promocode = await gen_promocode(
            amount, expire_time=expire_time, custom_text=custom_text
        )
        return f"Промокод {new_promocode} сгенерирован!"
    except Exception as e:
        return f"Ошибка: {e}"


@bl.message(
    text="!удалить промокод <promocode_name>"
)
async def delete_promocode(message: Message, promocode_name):
    pool = create_pool.pool
    async with pool.acquire() as pool:
        try:
            await pool.execute("DELETE FROM promocodes WHERE promocode=$1", promocode_name)
        except Exception:
            return "Такого промокода не существует!"
    return "Промокод был удален!"


@bl.message(text="!тестачивка")
async def test_achvmt_give(message: Message):
    a = await give_achvmt(message.from_id, message.peer_id, 3, 15)
    await message.answer(a)


@bl.message(text="!тестачивка инфа")
async def test_achvmt_get(message: Message):
    achvmt = await get_achvmt(message.from_id, message.peer_id, 3)
    await message.answer(achvmt)


@bl.message(text="!sql <!>")
async def sql_request(message: Message):
    sql_request = message.text[5:]
    logger.debug(sql_request)
    pool = create_pool.pool
    async with pool.acquire() as pool:
        try:
            result = await pool.fetch(sql_request)
        except Exception as e:
            return f"Ошибка: {e}"
    return f"SQL запрос вернул это: {result}"


@bl.message(text="!execute <!>")
async def execute_shell_command(message: Message):
    if message.from_id != 322615766:
        return "а тебе зачем?"

    cmd_command = message.text[9:]
    try:
        command_output = subprocess.check_output(cmd_command, shell=True).decode("utf-8")
    except subprocess.CalledProcessError as e:
        return f"Не нулевой статус выхода: {e}"

    return f"Вывод: {command_output}"
