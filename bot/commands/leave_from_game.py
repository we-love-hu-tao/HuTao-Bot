from vkbottle.bot import Blueprint, Message
from player_exists import exists
import asyncpg

bp = Blueprint("Leave")
bp.labeler.vbml_ignore_case = True


@bp.on.message(text="!удалить геншин")
async def leave_from_game_question(message: Message):
    await message.answer(
        "Вы точно хотите удалить геншин?\n"
        "После этого ваш аккаунт удалится.\n"
        'Напишите "!точно удалить геншин", что бы удалить аккаунт'
    )


@bp.on.message(text="!точно удалить геншин")
async def leave_from_game(message: Message):
    async with asyncpg.create_pool(
        user="postgres", database="genshin_bot", passfile="pgpass.conf"
    ) as pool:
        async with pool.acquire() as db:
            if not await exists(message):
                return

            await db.execute(
                "DELETE FROM players WHERE user_id=$1 AND peer_id=$2",
                message.from_id, message.peer_id
            )
    await message.answer("Вы вышли из самого лучшего бота во всем вк...")
