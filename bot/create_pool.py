import asyncpg
from loguru import logger


async def init():
    global pool
    logger.info("Creating pool for database")
    pool = await asyncpg.create_pool(
        user="postgres",
        database="hutao_bot",
        passfile="pgpass.conf"
    )

    async with pool.acquire() as db:
        # Players
        await db.execute('''
            CREATE TABLE IF NOT EXISTS public.players (
                user_id integer,
                peer_id integer,
                nickname VARCHAR(100),
                reward_last_time integer DEFAULT 0,
                doing_quest boolean DEFAULT false,
                daily_quests_time integer DEFAULT 0,
                uid integer,
                liked_posts_ids integer[] DEFAULT ARRAY[]::integer[],
                avatars jsonb DEFAULT '[]'::jsonb,
                inventory jsonb DEFAULT '[]'::jsonb,
                promocode text,
                has_redeemed_user_promocode boolean DEFAULT false,
                current_banner integer DEFAULT 100,
                gacha_records jsonb DEFAULT '[]'::jsonb,
                gacha_info jsonb DEFAULT '{}'::jsonb
            );
        ''')

        # Banned (table with banned users)
        await db.execute('''
            CREATE TABLE IF NOT EXISTS public.banned (
                user_id integer
            );
        ''')

        # Promocodes
        await db.execute('''
            CREATE TABLE IF NOT EXISTS public.promocodes (
                promocode text,
                author integer DEFAULT 0,
                expire_time integer DEFAULT 0,
                promocode_reward integer DEFAULT 800,
                redeemed_by integer[] DEFAULT '{}'::integer[]
            );
        ''')

        # Pictures (table with pictures ids in albums)
        await db.execute('''
            CREATE TABLE IF NOT EXISTS public.pictures (
                picture_name text,
                picture_id text
            );
        ''')
