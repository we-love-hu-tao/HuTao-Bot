from vkbottle.bot import Message
import create_pool


async def exists(event: Message, pool=None) -> bool:
    is_banned_request = "SELECT user_id FROM banned WHERE user_id=$1"
    exists_request = "SELECT user_id FROM players WHERE user_id=$1 AND peer_id=$2"

    if pool is not None:
        is_banned = await pool.fetchrow(is_banned_request, event.from_id)
        row = await pool.fetchrow(exists_request, event.from_id, event.peer_id)
    else:
        pool = create_pool.pool
        async with pool.acquire() as pool:
            is_banned = await pool.fetchrow(is_banned_request, event.from_id)
            row = await pool.fetchrow(exists_request, event.from_id, event.peer_id)

    if is_banned is None:  # Если пользователь не забанен
        if row is not None:  # Если пользователь существует
            return True
        else:
            await event.answer(
                "Для начала нужно зайти в Genshin Impact командой !начать"
            )
    else:
        await event.answer("нет (разбан у [id322615766|меня]).")
    return False
