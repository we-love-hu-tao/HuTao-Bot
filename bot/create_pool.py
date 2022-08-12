import asyncpg


async def init():
    global pool
    print("creating new pool")
    pool = await asyncpg.create_pool(
        user="postgres",
        database="genshin_bot",
        passfile="pgpass.conf"
    )


class Pool:
    pool = None

    async def get_pool(self):
        if self.pool is None:
            print("creating new pool")
            self.pool = await asyncpg.create_pool(
                user="postgres",
                database="genshin_bot",
                passfile="pgpass.conf"
            )
        return self.pool
