from vkbottle.bot import Message
import aiosqlite


async def exists(event: Message) -> bool:
    async with aiosqlite.connect("db.db") as db:
        async with db.execute(
            "SELECT banned FROM players WHERE user_id=(?)",
            (event.from_id,),
        ) as cur:
            result = await cur.fetchone()
    if result:
        if result[0] != 1:
            return True
        else:
            await event.answer("нет (жду извинений в [id322615766|лс]).")
    else:
        await event.answer(
            "Для начала нужно зайти в Genshin Impact командой !начать"
        )
    return False
