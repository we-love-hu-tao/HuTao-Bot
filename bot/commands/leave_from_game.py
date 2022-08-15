from vkbottle.bot import Blueprint, Message
import create_pool

bp = Blueprint("Leave")
bp.labeler.vbml_ignore_case = True


@bp.on.chat_message(text="!удалить геншин")
async def leave_from_game_question(message: Message):
    await message.answer(
        "Вы точно хотите удалить геншин?\n"
        "После этого ваш аккаунт удалится.\n"
        'Напишите "!точно удалить геншин", что бы удалить аккаунт'
    )


@bp.on.chat_message(text="!точно удалить геншин")
async def leave_from_game(message: Message):
    pool = create_pool.pool
    async with pool.acquire() as pool:

        await pool.execute(
            "DELETE FROM players WHERE user_id=$1 AND peer_id=$2",
            message.from_id, message.peer_id
        )
    await message.answer("Вы вышли из самого лучшего бота во всем вк...")
