from vkbottle.bot import Blueprint, Message

import create_pool
from item_names import ACQUAINT_FATE, INTERTWINED_FATE, PRIMOGEM
from keyboards import KEYBOARD_WISH
from utils import exists, get_item, give_item
from variables import EVENT_VARIANTS, STANDARD_VARIANTS

bp = Blueprint("Fates shop")
bp.labeler.vbml_ignore_case = True


@bp.on.chat_message(text=(
    "!купить молитвы <fate_type> <amount:int>",
    "!купить крутки <fate_type> <amount:int>",
    "[<!>|<!>] Купить молитвы <fate_type> <amount:int>"
))
async def buy_fates(message: Message, fate_type, amount: int):
    pool = create_pool.pool
    if not await exists(message):
        return

    if amount <= 0:
        return "Ты пьяный?"
    if amount >= 999999:
        return "За раз так много купить нельзя!"

    pay_count = 160 * amount
    wish_type = "стандартных"

    async with pool.acquire() as pool:
        primogems_count = (await get_item(PRIMOGEM, message.from_id, message.peer_id))['count']
        if primogems_count >= pay_count:
            if fate_type in STANDARD_VARIANTS:
                await give_item(message.from_id, message.peer_id, ACQUAINT_FATE, amount)
            elif fate_type in EVENT_VARIANTS:
                await give_item(message.from_id, message.peer_id, INTERTWINED_FATE, amount)
                wish_type = "ивентовых"
            else:
                return "Неа, таких молитв не существует!"

            await give_item(message.from_id, message.peer_id, PRIMOGEM, -pay_count)
            await message.answer(
                f"Вы купили {amount} {wish_type} молитв за {pay_count} примогемов!\n"
                f"Ваш баланс: {primogems_count - pay_count}",
                keyboard=KEYBOARD_WISH
            )
        else:
            return (
                f"Вам не хватает примогемов, {amount} молитв стоят "
                f"{pay_count} примогемов!"
            )
