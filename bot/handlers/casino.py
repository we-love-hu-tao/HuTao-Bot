from vkbottle.bot import BotLabeler, Message, rules

import create_pool
import random
from item_names import PRIMOGEM
from utils import exists, get_item, give_item

bl = BotLabeler()
bl.vbml_ignore_case = True

CAS_COLORS = {
    "красный": "red",
    "черный": "black",
    "зеленый": "green"
}


@bl.message(text="!рулетка <amount:int> <sel_color>")
async def casino_handler(message: Message, amount: int, sel_color):
    if not await exists(message):
        return

    primogems_count = (await get_item(PRIMOGEM, message.from_id, message.peer_id))['count']
    if primogems_count < amount:
        return "Вам не хватает примогемов!"
    if amount < 50:
        return "Че, боишься? Вы должны поставить как минимум 50 примогемов"
    if amount > 5600:
        return "Нельзя ставить так много, а то бомжом станешь!"

    sel_color = CAS_COLORS.get(sel_color)
    if sel_color is None:
        colors_types = ""
        for count, color in enumerate(CAS_COLORS):
            ending = ', '
            if count == len(CAS_COLORS)-1:
                ending = '.'
            colors_types += color+ending
        return f"Этого цвета не существует! Могут быть только такие варианты: {colors_types}"

    await give_item(message.from_id, message.peer_id, PRIMOGEM, -amount)

    # https://thecode.media/plotly/amp/
    ball = random.randint(1, 37)
    results = "Выпало "

    if ball in range(1, 19):
        color = "black"
        results += "&#9899;"
    elif ball in range(19, 36):
        color = "red"
        results += "&#128308;"
    else:
        color = "green"
        results += "&#128994;"
    results += f" {ball}\n"

    prim_count = 0
    if color == sel_color:
        match color:
            case "black" | "red":
                prim_count = amount * 2
            case _:
                prim_count = amount * 3

        await give_item(message.from_id, message.peer_id, PRIMOGEM, prim_count)

        results += f"&#127881; Вы выиграли {prim_count} примогемов!"
        return results

    return f"{results}&#128128; Вам не повезло и вы проиграли все свои примогемы! Может быть в следующий раз повезет..."

