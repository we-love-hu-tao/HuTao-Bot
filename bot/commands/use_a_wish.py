from vkbottle.bot import Blueprint, Message
from player_exists import HasAccount
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

    async def check_standard(self, min_=1) -> bool:
        """
        Проверяет, есть ли у игрока стандартное желание
        """
        async with aiosqlite.connect("db.db") as db:
            async with db.execute(
                "SELECT standard_wishes FROM players WHERE user_id=(?)",
                (self.user_id,),
            ) as cur:
                count = await cur.fetchone()
                if count[0] >= min_:
                    return True
                return False

    async def check_event(self, min_=1) -> bool:
        """
        Проверяет, есть ли у игрока ивентовое желание
        """
        async with aiosqlite.connect("db.db") as db:
            async with db.execute(
                "SELECT event_wishes FROM players WHERE user_id=(?)",
                (self.user_id,),
            ) as cur:
                count = await cur.fetchone()
                if count[0] >= min_:
                    return True
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
                        "UPDATE players SET rolls_standard=0 WHERE "
                        "user_id=(?)",
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

    async def decrease_wish(self, db, type_="standard", count=1):
        if type_ == "standard":
            await db.execute("UPDATE players SET standard_wishes=standard_wishes-(?) WHERE user_id=(?)", (count, self.user_id))
        elif type_ == "event":
            await db.execute("UPDATE players SET event_wishes=event_wishes-(?) WHERE user_id=(?)", (count, self.user_id))
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

    async def choose_gif(self, rarity, ten=False):
        if rarity == 3:
            # 3 star gif
            await self.message.answer(
                "Открываем...", attachment="doc-193964161_629778843"
            )
        elif rarity == 4:
            if ten:
                # 4 star gif 10 items
                await self.message.answer(
                    "Открываем...",
                    attachment="",
                )
            else:
                # 4 star gif
                await self.message.answer(
                    "Открываем...",
                    attachment="doc-193964161_629778865",
                )
        elif rarity == 5:
            if ten:
                # 5 star gif 10 times
                await self.message.answer(
                    "Открываем...",
                    attachment="",
                )
            else:
                # 5 star gif
                await self.message.answer(
                    "Открываем...",
                    attachment="doc-193964161_629110361",
                )

    async def roll(self, db, type) -> tuple:
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

            random_item = random.choice(list(type_rarity.items()))
            return random_item

        elif type == "event":
            current_event = "dance_of_lanterns"  # Текущий ивент

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
                for character in type_rarity.items():
                    if character[1]["event"] == current_event:
                        return character
                        break
            else:
                return random.choice(list(type_rarity.items()))


    async def use_wish(self, type):
        """
        Использует молитву
        """
        async with aiosqlite.connect("db.db") as db:
            await self.decrease_wish(db, type, 1)
            item_drop = await self.roll(db, type)
            type = item_drop[1]["type"]
            rarity = item_drop[1]["rarity"]
            name = item_drop[0]
            picture = item_drop[1]["picture"]

            await self.choose_gif(rarity)
            await asyncio.sleep(6.0)
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

    async def use_ten_wishes(self, roll_type):
        async with aiosqlite.connect("db.db") as db:
            item_drops = []
            output = ""
            five_star = False
            await self.decrease_wish(db, roll_type, 10)
            for i in range(0,10):
                new_drop = await self.roll(db, roll_type)
                item_drops.append(new_drop)
                item_type = item_drops[i][1]["type"]
                item_rarity = item_drops[i][1]["rarity"]
                if item_rarity == 5:
                    five_star = True
                item_name = item_drops[i][0]
                if item_type == "weapon":
                    output+=f"Выпало оружие {item_name} ({'★' * item_rarity})!\n"
                elif item_type == "character":
                    output+=f"Выпал персонаж {item_name} ({'★' * item_rarity})!\n"
            if five_star:
                await self.choose_gif(5, True)
            else:
                await self.choose_gif(4, True)
            await asyncio.sleep(6.0)
            await self.message.answer(output)
            


@bp.on.message(HasAccount(), text="!помолиться стандарт")
async def standard_wish(message: Message):
    wish = Wish(message.from_id, message)
    if await wish.check_standard():
        await wish.use_wish("standard")
    else:
        await message.answer(
            "У вас нет судьбоносных встреч! Ждите следующего дня"
        )


@bp.on.message(HasAccount(), text="!помолиться стандарт 10")
async def standard_wish(message: Message):
    wish = Wish(message.from_id, message)
    if await wish.check_standard(10):
        await wish.use_ten_wishes("standard")
    else:
        await message.answer(
            "У вас не хватает судьбоносных встреч! Ждите следующего дня"
        )


@bp.on.message(HasAccount(), text=("!помолиться событие", "!помолиться ивент"))
async def event_wish(message: Message):
    wish = Wish(message.from_id, message)
    if await wish.check_event():
        await wish.use_wish("event")
    else:
        await message.answer(
            "У вас нет переплетающих судьб! Ждите следующего дня"
        )


@bp.on.message(HasAccount(), text=("!помолиться событие 10", "!помолиться ивент 10"))
async def event_wish(message: Message):
    wish = Wish(message.from_id, message)
    if await wish.check_event(10):
        await wish.use_ten_wishes("event")
    else:
        await message.answer(
            "У вас не хватает переплетающих судьб! Ждите следующего дня"
        )
