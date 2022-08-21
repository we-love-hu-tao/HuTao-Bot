from loguru import logger
import asyncpg


async def init():
    global pool
    logger.info("Создание пулла для базы данных")
    pool = await asyncpg.create_pool(
        user="postgres",
        database="genshin_bot",
        passfile="pgpass.conf"
    )
