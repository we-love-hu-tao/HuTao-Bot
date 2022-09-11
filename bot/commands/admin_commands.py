from vkbottle.bot import Blueprint, Message
from vkbottle.dispatch.rules import ABCRule
from loguru import logger
from typing import Optional
from utils import give_exp, gen_promocode
import time
import subprocess
import create_pool

bp = Blueprint("Admin")
bp.labeler.vbml_ignore_case = True

admin_list = (322615766, 328328155)


class AdminRule(ABCRule[Message]):
    async def check(self, event: Message) -> bool:
        return event.from_id in admin_list


@bp.on.message(AdminRule(), text="!беседы <mention>")
async def list_user_chat(message: Message, mention):
    mention_id = int(mention.split("|")[0][1:].replace("id", ""))
    pool = create_pool.pool
    async with pool.acquire() as pool:
        raw_chats = await pool.fetch(
            "SELECT peer_id FROM players WHERE user_id=$1", mention_id
        )

    to_send = f"Айди бесед [id{mention_id}|этого] пользователя:\n"
    for chat in raw_chats:
        to_send += f"{chat['peer_id']}\n"

    return to_send


@bp.on.message(AdminRule(), text=(
    "+примогемы <amount:int>",
    "+примогемы <amount:int> <mention> <peer_id:int>"
))
async def give_wish(
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
            logger.info(f"Добавление пользователю {mention_id} {amount} примогемов")
            await pool.execute(
                "UPDATE players SET primogems=primogems+$1 WHERE user_id=$2 AND peer_id=$3",
                amount, mention_id, peer_id
            )
            return f"[id{mention_id}|Этому пользователю] было добавлено {amount} примогемов"
        else:
            return "Такого пользователя нет в игре!"


@bp.on.message(AdminRule(), text=(
    "+уровень <amount:int>",
    "+уровень <amount:int> <mention> <peer_id>"
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
            logger.info(f"Добавление пользователю {mention_id} {amount} experience")

            await give_exp(amount, mention_id, peer_id, bp.api)

            return f"[id{mention_id}|Этому пользователю] было добавлено {amount} experience!"
        else:
            return "Такого пользователя нет в игре!"


@bp.on.message(AdminRule(), text=("!гнш бан <mention>", "!гнш бан"))
async def ban_user(message: Message, mention):
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


@bp.on.message(AdminRule(), text=("!гнш разбан <mention>", "!гнш разбан"))
async def unban_user(message: Message, mention):
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


@bp.on.message(
    AdminRule(),
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


@bp.on.message(
    AdminRule(), text="!удалить промокод <promocode_name>"
)
async def delete_promocode(message: Message, promocode_name):
    pool = create_pool.pool
    async with pool.acquire() as pool:
        try:
            await pool.execute("DELETE FROM promocodes WHERE promocode=$1", promocode_name)
        except Exception:
            return "Такого промокода не существует!"
    return "Промокод был удален!"


@bp.on.message(AdminRule(), text="!sql <!>")
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


@bp.on.message(AdminRule(), text="!execute <!>")
async def execute_shell_command(message: Message):
    if message.from_id != 322615766:
        return "а тебе зачем?"

    cmd_command = message.text[9:]
    command_output = subprocess.run(["powershell", "-Command", cmd_command], capture_output=True)
    if command_output.returncode != 0:
        return f"Ошибка: {command_output.stderr}"
    return f"Команда вернула это: {command_output.stdout.decode('utf-8')}"
