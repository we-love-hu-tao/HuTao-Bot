from vkbottle.bot import Blueprint, Message
import aiosqlite
import asyncio
import drop
import random

bp = Blueprint('Use wish')
bp.labeler.vbml_ignore_case = True


class Wish:
    def __init__(self, user_id: int, message: Message):
        self.user_id = user_id
        self.message = message

    async def player_registered(self) -> bool:
        """
        Проверяет, зарегестрировался ли игрок
        """
        async with aiosqlite.connect("db.db") as db:
            async with db.execute(
                "SELECT user_id FROM players WHERE user_id=(?)",
                (self.user_id,),
            ) as cur:
                exists = await cur.fetchone()
                if exists:
                    return True
                else:
                    return False

    async def check_standard(self) -> bool:
        """
        Проверяет, есть ли у игрока стандартное желание
        """
        async with aiosqlite.connect("db.db") as db:
            async with db.execute(
                "SELECT standard_wishes FROM players WHERE user_id=(?)",
                (self.user_id,),
            ) as cur:
                count = await cur.fetchone()
                if count[0] > 0:
                    return True
                else:
                    return False

    async def check_event(self) -> bool:
        """
        Проверяет, есть ли у игрока ивентовое желание
        """
        async with aiosqlite.connect("db.db") as db:
            async with db.execute(
                "SELECT event_wishes FROM players WHERE user_id=(?)",
                (self.user_id,),
            ) as cur:
                count = await cur.fetchone()
                if count[0] > 0:
                    return True
                else:
                    return False

    def chance(self, num: float) -> bool:
        """
        Возварщает шанс
        >>> chance(50.0)
        >>> True
        """
        return True if random.random() * 100 < num else False

    async def reset_rolls_count(self, wish="standard", type="rare"):
        """
        Обнуляет количество стандартных/ивентовых прокруток у игрока
        """
        async with aiosqlite.connect("db.db") as db:
            if wish == "standard":
                if type == "rare":
                    await db.execute(
                        "UPDATE players SET rolls_standard=0 WHERE"
                        " user_id=(?)",
                        (self.user_id,),
                    )
                elif type == "legendary":
                    await db.execute(
                        "UPDATE players SET legendary_rolls_standard=0 WHERE "
                        "user_id=(?)",
                        (self.user_id,),
                    )
            elif wish == "event":
                if type == "rare":
                    await db.execute(
                        "UPDATE players SET rolls_event=0 WHERE user_id=(?)",
                        (self.user_id,),
                    )
                elif type == "legendary":
                    await db.execute(
                        "UPDATE players SET legendary_rolls_event=0 WHERE "
                        "user_id=(?)",
                        (self.user_id,),
                    )
            await db.commit()

    async def increase_rolls_count(self, wish="standard"):
        """
        Увеличивает количество прокруток стандартной/ивентовой молитвы
        """
        async with aiosqlite.connect("db.db") as db:
            if wish == "standard":
                await db.execute(
                    "UPDATE players SET "
                    "legendary_rolls_standard=legendary_rolls_standard+1 "
                    "WHERE user_id=(?)",
                    (self.user_id,),
                )
                await db.execute(
                    "UPDATE players SET rolls_standard=rolls_standard+1 WHERE "
                    "user_id=(?)",
                    (self.user_id,),
                )
            else:
                await db.execute(
                    "UPDATE players SET rolls_event=rolls_event+1 WHERE "
                    "user_id=(?)",
                    (self.user_id,),
                )
                await db.execute(
                    "UPDATE players SET "
                    "legendary_rolls_event=legendary_rolls_event+1 WHERE "
                    "user_id=(?)",
                    (self.user_id,),
                )
            await db.commit()

    async def use_wish(self, type):
        """
        Использует молитву
        """
        async with aiosqlite.connect("db.db") as db:
            async with db.execute(
                """SELECT
                rolls_standard,
                legendary_rolls_standard,
                rolls_event,
                legendary_rolls_event
                FROM players WHERE user_id=(?)""",
                (self.user_id,),
            ) as cur:
                count = await cur.fetchone()
                rolls_standard_count = count[0]
                legendary_rolls_standard_count = count[1]
                rolls_event_count = count[2]
                legendary_rolls_event_count = count[3]

            if type == "standard":
                await db.execute(
                    "UPDATE players SET standard_wishes=standard_wishes-1 "
                    "WHERE user_id=(?)",
                    (self.user_id,),
                )
                await db.commit()

                if self.chance(1.6) or legendary_rolls_standard_count >= 89:
                    await self.reset_rolls_count(type="legendary")
                    type_rarity = random.choice(
                        (
                            drop.legendary_standard_characters,
                            drop.legendary_standard_weapons,
                        )
                    )
                elif self.chance(13.0) or rolls_standard_count >= 9:
                    await self.reset_rolls_count()
                    type_rarity = random.choice(
                        (
                            drop.rare_standard_characters,
                            drop.rare_standard_weapons,
                        )
                    )
                else:
                    await self.increase_rolls_count()
                    type_rarity = drop.normal_standard_weapons

                item_drop = random.choice(list(type_rarity.items()))
                type = item_drop[1]["type"]
                rarity = item_drop[1]["rarity"]
                name = item_drop[0]
                picture = item_drop[1]["picture"]
            elif type == "event":
                current_event = "moment_of_bloom"  # Текущий ивент

                # Отнятие одной ивентовой молитвы
                await db.execute(
                    "UPDATE players SET event_wishes=event_wishes-1 WHERE "
                    "user_id=(?)",
                    (self.user_id,),
                )
                await db.commit()

                if self.chance(1.6) or legendary_rolls_event_count >= 89:
                    # 5 звездочный персонаж
                    await self.reset_rolls_count(
                        wish="event", type="legendary"
                    )
                    type_rarity = random.choice(
                        (
                            drop.legendary_event_characters,
                            drop.legendary_standard_characters,
                        )
                    )

                elif self.chance(13.0) or rolls_event_count >= 9:
                    # 4 звездочный персонаж/оружие
                    await self.reset_rolls_count(wish="event")
                    type_rarity = random.choice(
                        (
                            drop.rare_standard_characters,
                            drop.rare_standard_weapons,
                        )
                    )
                else:
                    # Стандартное оружие
                    # Увеличение числа для получения гаранта
                    await self.increase_rolls_count("event")
                    type_rarity = drop.normal_standard_weapons

                if type_rarity == drop.legendary_event_characters:
                    leg_event = drop.legendary_event_characters
                    for character in leg_event:
                        if leg_event[character]["event"] == current_event:
                            item_drop = leg_event[character].items()
                            name = character
                            break
                else:
                    item_drop = random.choice(list(type_rarity.items()))

                type = item_drop[1]["type"]
                rarity = item_drop[1]["rarity"]
                name = item_drop[0]
                picture = item_drop[1]["picture"]

            if rarity == 3:
                # 3 star gif
                await self.message.answer(
                    "Открываем...", attachment="doc-193964161_629778843"
                )
            elif rarity == 4:
                # 4 star gif
                await self.message.answer(
                    "Открываем...",
                    attachment="doc-193964161_629778865",
                )
            elif rarity == 5:
                # 5 star gif
                await self.message.answer(
                    "Открываем...",
                    attachment="doc-193964161_629110361",
                )
            await asyncio.sleep(6)

            if type == "weapon":
                await self.message.answer(
                    f"Выпало оружие {name} ({'★' * rarity})!",
                    attachment=picture,
                )
            elif type == "character":
                await self.message.answer(
                    f"Выпал персонаж {name} ({'★' * rarity})!",
                    attachment=picture,
                )
            await db.commit()


@bp.on.message(command="помолиться стандарт")
async def standard_wish(message: Message):
    wish = Wish(message.from_id, message)
    if await wish.player_registered():
        if await wish.check_standard():
            print("using standard wish")
            await wish.use_wish("standard")
        else:
            await message.answer(
                "У вас нет судьбоносных встреч! Ждите следующего дня"
            )
    else:
        await message.answer(
            "Для начала нужно зайти в genshin impact командой !начать"
        )


@bp.on.message(text=("!помолиться событие", "!помолиться ивент"))
async def event_wish(message: Message):
    wish = Wish(message.from_id, message)
    if await wish.player_registered():
        if await wish.check_event():
            await wish.use_wish("event")
        else:
            await message.answer(
                "У вас нет переплетающихся судьб! Ждите следующего дня"
            )
    else:
        await message.answer(
            "Для начала нужно зайти в genshin impact командой !начать"
        )
