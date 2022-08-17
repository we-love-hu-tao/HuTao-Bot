from vkbottle.bot import Blueprint, Message
import create_pool

bp = Blueprint("Fates shop")
bp.labeler.vbml_ignore_case = True


@bp.on.chat_message(command=("магазин", "shop"))
async def shop(message: Message):
    await message.answer(
        "Добро пожаловать в магазин паймон!\n"
        "Цена молитв - 160 примогемов"
    )


@bp.on.chat_message(text="!купить молитвы <fate_type> <amount:int>")
async def buy_fates(message: Message, fate_type, amount: int):
    pool = create_pool.pool
    async with pool.acquire() as pool:
        if amount <= 0:
            await message.answer("Ты пьяный?")
            return

        primogems = await pool.fetchrow(
            "SELECT primogems FROM players WHERE user_id=$1 AND peer_id=$2",
            message.from_id, message.peer_id,
        )
        if primogems[0] >= 160 * amount:
            if fate_type == "стандарт":
                await pool.execute(
                    "UPDATE players SET primogems=primogems-$1, "
                    "standard_wishes=standard_wishes+$2 WHERE user_id=$3 AND "
                    "peer_id=$4",
                    160 * amount, amount, message.from_id, message.peer_id,
                )
                await message.answer(
                    f"Вы купили {amount} стандартных молитв за "
                    f"{amount*160} примогемов!"
                )
            elif fate_type == "ивент":
                await pool.execute(
                    "UPDATE players SET primogems=primogems-$1, "
                    "event_wishes=event_wishes+$2 WHERE user_id=$3 AND "
                    "peer_id=$4",
                    160 * amount, amount, message.from_id, message.peer_id,
                )
                await message.answer(
                    f"Вы купили {amount} ивентовых молитв за "
                    f"{amount*160} примогемов!"
                )
            else:
                await message.answer("Неа, таких молитв не существует")

        else:
            await message.answer(
                f"Вам не хватает примогемов, {amount} молитв стоят "
                f"{amount*160} примогемов!"
            )
