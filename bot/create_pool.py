from loguru import logger
import asyncpg


async def init():
    global pool
    logger.debug("creating new pool")
    pool = await asyncpg.create_pool(
        user="postgres",
        database="genshin_bot",
        passfile="pgpass.conf"
    )
