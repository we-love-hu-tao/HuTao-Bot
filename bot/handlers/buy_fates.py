from vkbottle.bot import BotLabeler, Message

import create_pool
from item_names import ACQUAINT_FATE, INTERTWINED_FATE, PRIMOGEM
from keyboards import KEYBOARD_WISH
from utils import exists, get_item, give_item, translate
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
        return await translate("shop", "zero_value")
    if amount > 99999:
        return await translate("shop", "too_big_value")

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
                return await translate("shop", "unknown_wish")

            await give_item(message.from_id, message.peer_id, PRIMOGEM, -pay_count)
            current_balance = primogems_count - pay_count
            await message.answer(
                (await translate("shop", "buy_confirmation"))
                .format(
                    amount=amount,
                    wish_type=wish_type,
                    pay_count=pay_count,
                    current_balance=current_balance
                ),
                keyboard=KEYBOARD_WISH
            )
        else:
            return (
                (await translate("shop", "not_enough_primos"))
                .format(amount=amount, pay_count=pay_count)+'\n'
                + await translate("shop", "not_enough_primos_tip")
            )
