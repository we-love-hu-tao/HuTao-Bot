from vkbottle.bot import Bot
from vkbottle import load_blueprints_from_package
import aiosqlite
import asyncio


async def create_table():
    async with aiosqlite.connect("db.db") as db:
        await db.execute("""CREATE TABLE IF NOT EXISTS players (
            user_id INTEGER,
            standard_wishes INTEGER DEFAULT 5,
            event_wishes INTEGER DEFAULT 5
        )""")
asyncio.get_event_loop().run_until_complete(create_table())

token = "eaa6b0d5e288c9b4cf51178141422ab46e142c39b319530f2ff567f8703be9e3a3388adf1b3a4079864b6"  # noqa: E501
bot = Bot(token=token)

for bp in load_blueprints_from_package("commands"):
    bp.load(bot)

bot.run_forever()
