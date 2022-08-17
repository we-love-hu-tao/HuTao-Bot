from vkbottle.bot import Message
from vkbottle import BaseMiddleware
from loguru import logger
import create_pool

is_banned_request = "SELECT user_id FROM banned WHERE user_id=$1"
exists_request = "SELECT user_id FROM players WHERE user_id=$1 AND peer_id=$2"


class PlayerExists(BaseMiddleware[Message]):
    def __init__(self, event, view):
        super().__init__(event, view)

    async def pre(self):
        """
        if event.text.lower() != "!начать":  # 2000000014 - id только тру челики
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
                await event.answer(
                    "нет (разбан у [id322615766|меня])."
                )
        else:
            return True
        return False
        """
        logger.debug("-----------------------")
        logger.debug(self.handle_responses)
        logger.debug(self.view)
        logger.debug("-----------------------")
