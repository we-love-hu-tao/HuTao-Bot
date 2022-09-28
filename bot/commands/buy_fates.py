from vkbottle.bot import Blueprint, Message
from player_exists import exists
from variables import STANDARD_VARIANTS, EVENT_VARIANTS
from item_names import PRIMOGEM, INTERTWINED_FATE, ACQUAINT_FATE
from utils import give_item, get_item
import create_pool

bp = Blueprint("Fates shop")
bp.labeler.vbml_ignore_case = True


@bp.on.chat_message(text=(
    "!купить молитвы <fate_type> <amount:int>",
    "!купить крутки <fate_type> <amount:int>",
))
async def buy_fates(message: Message, fate_type, amount: int):
    pool = create_pool.pool
    if not await exists(message):
        return
    async with pool.acquire() as pool:
        if amount <= 0:
            return "Ты пьяный?"

        if amount >= 999999:
            return "За раз так много купить нельзя!"

        primogems = await get_item(PRIMOGEM, message.from_id, message.peer_id)
        wish_type = "стандартных"
        if primogems['count'] >= 160 * amount:
            if fate_type in STANDARD_VARIANTS:
                await give_item(message.from_id, message.peer_id, ACQUAINT_FATE, amount)
            elif fate_type in EVENT_VARIANTS:
                await give_item(message.from_id, message.peer_id, INTERTWINED_FATE, amount)
                wish_type = "ивентовых"
            else:
                return "Неа, таких молитв не существует!"

            await give_item(message.from_id, message.peer_id, PRIMOGEM, -(160 * amount))
            await message.answer(
                f"Вы купили {amount} {wish_type} молитв за "
                f"{160 * amount} примогемов!"
            )
        else:
            await message.answer(
                f"Вам не хватает примогемов, {amount} молитв стоят "
                f"{160 * amount} примогемов!"
            )
