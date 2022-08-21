from vkbottle.bot import Blueprint, Message
from player_exists import exists
from loguru import logger
import create_pool

bp = Blueprint("Leave")
bp.labeler.vbml_ignore_case = True


@bp.on.chat_message(text="!удалить геншин")
async def leave_from_game_question(message: Message):
    if not await exists(message):
        return
    await message.answer(
        "Вы точно хотите удалить геншин?\n"
        "После этого ваш аккаунт удалится.\n"
        'Напишите "!точно удалить геншин", что бы удалить аккаунт'
    )


@bp.on.chat_message(text="!точно удалить геншин")
async def leave_from_game(message: Message):
    if not await exists(message):
        return
    pool = create_pool.pool
    async with pool.acquire() as pool:
        logger.info(
            f"Пользователь {message.from_id} удалил аккаунт в беседе {message.peer_id}, кринж"
        )
        await pool.execute(
            "DELETE FROM players WHERE user_id=$1 AND peer_id=$2",
            message.from_id, message.peer_id
        )
    await message.answer("Вы вышли из самого лучшего бота во всем вк...")
