from loguru import logger
import asyncpg

table_players = {
    "user_id": {
        "data_type": "integer",
        "default": None
    },
    "peer_id": {
        "data_type": "integer",
        "default": None
    },
    "nickname": {
        "data_type": "text",
        "default": None
    },
    "reward_last_time": {
        "data_type": "integer",
        "default": "0"
    },
    "doing_quest": {
        "data_type": "boolean",
        "default": 'false'
    },
    "daily_quests_time": {
        "data_type": "integer",
        "default": "0"
    },
    "gacha_records": {
        "data_type": "jsonb",
        "default": "'[]'::jsonb"
    },
    "uid": {
        "data_type": "integer",
        "default": None
    },
    "liked_posts_ids": {
        "data_type": "ARRAY",
        "default": "ARRAY[]::integer[]"
    },
    "avatars": {
        "data_type": "jsonb",
        "default": "'[]'::jsonb"
    },
    "inventory": {
        "data_type": "jsonb",
        "default": "'[]'::jsonb"
    },
    "promocode": {
        "data_type": "text",
        "default": None
    },
    "has_redeemed_user_promocode": {
        "data_type": "boolean",
        "default": "false"
    },
    "current_banner": {
        "data_type": "integer",
        "default": "100"
    },
    "gacha_info": {
        "data_type": "jsonb",
        "default": "'{}'::jsonb"
    },
}


async def init():
    global pool
    logger.info("Creating pool for database")
    pool = await asyncpg.create_pool(
        user="postgres",
        database="hutao_bot",
        passfile="pgpass.conf"
    )

    async with pool.acquire() as db:
        # Проверка таблицы
        tables = []
        tables.append(
            await db.fetch(
                "SELECT * FROM information_schema.columns WHERE table_name='players'"
            )
        )
        tables.append(
            await db.fetch(
                "SELECT * FROM information_schema.columns WHERE table_name='banned'"
            )
        )
        tables.append(
            await db.fetch(
                "SELECT * FROM information_schema.columns WHERE table_name='promocodes'"
            )
        )
        tables.append(
            await db.fetch(
                "SELECT * FROM information_schema.columns WHERE table_name='pictures'"
            )
        )

        for table in tables:
            if len(table) == 0:
                raise ValueError("Some tables doesn't exists, bot can't continue without them!")

        player_records = tables[0]

        unknown_records = []
        for player_record in player_records:
            if player_record['column_name'] not in table_players:
                unknown_records.append(
                    (player_record['column_name'], player_record['data_type'])
                )
                continue

        if len(unknown_records) > 0:
            logger.warning(
                "There are unknown values in the database:"
            )
            for unknown_record in unknown_records:
                logger.warning(f"{unknown_record[0]}: {unknown_record[1]}")

        for column in table_players.items():
            command_exists = False
            right_type = False
            right_default = False

            for player_record in player_records:
                if player_record['column_name'] == column[0]:
                    command_exists = True
                    if player_record['data_type'] == column[1]['data_type']:
                        right_type = True
                        if player_record['column_default'] == column[1]['default']:
                            right_default = True

            if command_exists and right_type and right_default:
                logger.info(
                    f"Столбец {column[0]} с типом {column[1]['data_type']} "
                    f"(дефолтное значение - {column[1]['default']}) прошел проверку"
                )
            elif not command_exists:
                logger.warning(
                    f"Столбца {column[0]} с типом {column[1]['data_type']} не существует, "
                    "но возможно бот может продолжить без него (но с багами)"
                )

            elif not right_type:
                logger.warning(
                    f"Столбец {column[0]} существует, но с "
                    f"неправильным типом (должен быть {column[1]['data_type']})"
                )

            elif not right_default:
                logger.warning(
                    f"Столбец {column[0]} существует, но с "
                    f"неправильным дефолтным значением (должен быть {column[1]['default']})"
                )
