from vkbottle.bot import Message
from vkbottle.dispatch.rules import ABCRule
import aiosqlite


class HasAccount(ABCRule[Message]):
    async def check(self, event: Message) -> bool:
        async with aiosqlite.connect("db.db") as db:
            async with db.execute(
                "SELECT EXISTS (SELECT * FROM players WHERE user_id=(?))",
                (event.from_id,),
            ) as cur:
                result = await cur.fetchone()
        if result[0]:
            return True
        else:
            await event.answer(
                "Для начала нужно зайти в Genshin Impact командой !начать"
            )
            return False
