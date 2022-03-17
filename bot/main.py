from vkbottle.bot import Bot
from vkbottle import load_blueprints_from_package
import aiosqlite
import asyncio
import loguru  # noqa: F401


async def create_table():
    async with aiosqlite.connect("db.db") as db:
        await db.execute("""CREATE TABLE IF NOT EXISTS players (
            user_id INTEGER,
            nickname TEXT,
            photo_link TEXT,
            reward_last_time INTEGER DEFAULT 0,
            standard_wishes INTEGER DEFAULT 5,
            event_wishes INTEGER DEFAULT 5,
            rolls_standard INTEGER DEFAULT 0,
            legendary_rolls_standard INTEGER DEFAULT 0,
            rolls_event INTEGER DEFAULT 0,
            legendary_rolls_event INTEGER DEFAULT 0,
            did_quest_today INTEGER DEFAULT 0,
            doing_quest INTEGER DEFAULT 0,
            daily_quests_time INTEGER DEFAULT 0
        )""")
asyncio.get_event_loop().run_until_complete(create_table())

token = "eaa6b0d5e288c9b4cf51178141422ab46e142c39b319530f2ff567f8703be9e3a3388adf1b3a4079864b6"  # noqa: E501
bot = Bot(token=token)

for bp in load_blueprints_from_package("commands"):
    bp.load(bot)

bot.run_forever()
