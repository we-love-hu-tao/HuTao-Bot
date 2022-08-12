import asyncpg
import asyncio


async def main():
    async with asyncpg.create_pool(
        user="postgres", database="genshin_bot", passfile="pgpass.conf"
    ) as pool:
        async with pool.acquire() as pool:
            history_type = "event_rolls_history"
            from_id = 322615766
            peer_id = 2000000003
            result = await pool.fetchrow(
                "SELECT $1 FROM players WHERE user_id=$2 AND peer_id=$3",
                history_type, from_id, peer_id
            )
            print(result)

asyncio.run(main())
