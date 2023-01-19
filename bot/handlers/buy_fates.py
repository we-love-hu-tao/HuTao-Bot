from vkbottle.bot import BotLabeler, Message, rules

import create_pool
from item_names import ACQUAINT_FATE, INTERTWINED_FATE, PRIMOGEM
from keyboards import KEYBOARD_WISH
from utils import exists, get_item, give_item
from variables import EVENT_VARIANTS, STANDARD_VARIANTS

bl = BotLabeler()
bl.vbml_ignore_case = True


@bl.message(text=(
    "!купить молитвы <fate_type> <amount:int>",
    "!купить крутки <fate_type> <amount:int>",
    "!купить молитвы все <fate_type>",
    "!купить крутки все <fate_type>",
    "[<!>|<!>] Купить молитвы <fate_type> <amount:int>",
    "Купить молитвы <fate_type> <amount:int>",
))
async def buy_fates(message: Message, fate_type, amount: int = -1):
    pool = create_pool.pool
    if not await exists(message):
        return

    if amount == 0:
        return "Ты пьяный?"
    if amount > 99999:
        return "За раз так много купить нельзя!"

    primogems_count = (await get_item(PRIMOGEM, message.from_id, message.peer_id))['count']
    if amount == -1:
        amount = primogems_count // 160

    pay_count = 160 * amount
    wish_type = "стандартных"

    async with pool.acquire() as pool:
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
                f"{pay_count} примогемов.\n"
                "Вы также можете использовать \"!купить молитвы все <тип молитвы>\", "
                "что бы купить молитвы на все примогемы!"
            )
