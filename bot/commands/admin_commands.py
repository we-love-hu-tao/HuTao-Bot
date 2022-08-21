from vkbottle.bot import Blueprint, Message
from vkbottle.dispatch.rules import ABCRule
from loguru import logger
from typing import Optional
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
    if mention is not None:
        mention_id = int(mention.split("|")[0][1:].replace("id", ""))
    else:
        mention_id = message.from_id

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


@bp.on.message(AdminRule(), text="!гнш бан <mention>")
async def ban_user(message: Message, mention):
    mention_id = int(mention.split("|")[0][1:].replace("id", ""))
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


@bp.on.message(AdminRule(), text="!гнш разбан <mention>")
async def unban_user(message: Message, mention):
    mention_id = int(mention.split("|")[0][1:].replace("id", ""))
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
