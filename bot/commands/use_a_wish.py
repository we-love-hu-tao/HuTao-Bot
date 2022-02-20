from vkbottle.bot import Blueprint, Message
from vkbottle import DocMessagesUploader
import aiosqlite
import asyncio
import random
import drop

bp = Blueprint("Wish command")
bp.labeler.vbml_ignore_case = True


@bp.on.message(command="помолиться стандарт")
async def standart_wish(message: Message):
    async with aiosqlite.connect("db.db") as db:
        async with db.execute(
            "SELECT standart_wishes FROM players WHERE user_id = ?",
            (message.from_id,),
        ) as cur:
            count = await cur.fetchone()
            if count:
                if count[0] >= 1:
                    print("new wish")
                    await db.execute(
                        "UPDATE players SET standart_wishes = standart_wishes"
                        " - 1 WHERE user_id = (?)",
                        (message.from_id,),
                    )
                    print("choicing type...")
                    type_drop = random.choice(
                        (
                            drop.normal_standard_weapons,
                            drop.rare_standard_weapons,
                            drop.legendary_standard_weapons,
                            drop.rare_standard_characters,
                            drop.legendary_standard_characters,
                        )
                    )
                    print("choicing item...")
                    item_drop = random.choice(list(type_drop.items()))
                    type = item_drop[1]["type"]
                    rarity = item_drop[1]["rarity"]
                    name = item_drop[0]
                    print("comparing...")
                    print(item_drop)
                    if rarity == 3:
                        # 3 star gif
                        await message.answer("Открываем...")
                    elif rarity == 4:
                        # 4 star gif
                        await message.answer("Открываем...")
                    elif rarity == 5:
                        # 5 star gif
                        await message.answer(
                            "Открываем...", attachment="doc-193964161_629110361"
                            )
                    else:
                        print(rarity)
                    await asyncio.sleep(5.8)
                    if type == "weapon":
                        await message.answer(f"Выпало оружие {name} ({'★' * rarity})!")
                    elif type == "character":
                        await message.answer(f"Выпал персонаж {name} ({'★' * rarity})!")
                else:
                    await message.answer(
                        "У вас закончились стандартные молитвы! Ждите "
                        "следующего дня"
                    )
                await db.commit()
            else:
                await message.answer(
                    "Для начала надо зайти в genshin impact командой !начать"
                )
