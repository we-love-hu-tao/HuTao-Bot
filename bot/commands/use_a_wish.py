from vkbottle.bot import Blueprint, Message
import aiosqlite
import asyncio
import random
import drop

bp = Blueprint("Wish command")
bp.labeler.vbml_ignore_case = True


class Wish:
    def __init__(self, user_id: int, message: Message):
        self.user_id = user_id
        self.message = message

    async def player_registered(self, db):
        async with aiosqlite.connect("db.db") as db:
            async with db.execute(
                "SELECT user_id FROM players WHERE user_id = (?)",
                (self.user_id,),
            ) as cur:
                exists = await cur.fetchone()
                if exists:
                    return True
                else:
                    return False

    async def check_standard(self, db):
        async with aiosqlite.connect("db.db") as db:
            async with db.execute(
                "SELECT standard_wishes FROM players WHERE user_id = ?",
                (self.user_id,),
            ) as cur:
                count = await cur.fetchone()
                if count:
                    return True
                else:
                    return False

    async def check_event(self, db):
        async with aiosqlite.connect("db.db") as db:
            async with db.execute(
                "SELECT event_wishes FROM players WHERE user_id = ?",
                (self.user_id,),
            ) as cur:
                count = await cur.fetchone()
                if count:
                    return True
                else:
                    return False

    async def chance(self, num: float):
        if random.random() * 100 < num:
            return True
        else:
            return False

    async def use_wish(self, db, type):
        async with aiosqlite.connect("db.db") as db:
            if type == "standard":
                await db.execute(
                    "UPDATE players SET standard_wishes=standard_wishes-1"
                    " WHERE user_id=(?)",
                    (self.user_id,),
                )
                if await self.chance(1.6):
                    type_rarity = random.choice(
                        (
                            drop.legendary_standard_characters,
                            drop.legendary_standard_weapons,
                        )
                    )
                elif await self.chance(13.0):
                    type_rarity = random.choice(
                        (
                            drop.rare_standard_characters,
                            drop.rare_standard_weapons,
                        )
                    )
                else:
                    type_rarity = drop.normal_standard_weapons

                item_drop = random.choice(list(type_rarity.items()))
                type = item_drop[1]["type"]
                rarity = item_drop[1]["rarity"]
                name = item_drop[0]
                picture = item_drop[1]["picture"]
            elif type == "event":
                current_event = "everbloom_violet"

                await db.execute(
                    "UPDATE players SET event_wishes=event_wishes-1 WHERE "
                    "user_id=(?)",
                    (self.user_id,),
                )
                type_rarity = random.choice(
                    (
                        drop.normal_standard_weapons,
                        drop.rare_standard_weapons,
                        drop.rare_standard_characters,
                        drop.legendary_standard_characters,
                        drop.legendary_event_characters,
                    )
                )

                if type_rarity == drop.legendary_event_characters:
                    leg_event = drop.legendary_event_characters
                    for character in leg_event:
                        if leg_event[character]["event"] == current_event:
                            item_drop = leg_event[character]
                            name = character
                else:
                    item_drop = random.choice(list(type_rarity.items()))
                    type = item_drop[1]["type"]
                    rarity = item_drop[1]["rarity"]
                    name = item_drop[0]
                    picture = item_drop[1]["picture"]

        if rarity == 3:
            # 3 star gif
            await self.message.answer(
                "Открываем...", attachment="doc-193964161_629438630"
            )
        elif rarity == 4:
            # 4 star gif
            await self.message.answer(
                "Открываем...",
                attachment="doc-193964161_629435717",
            )
        elif rarity == 5:
            # 5 star gif
            await self.message.answer(
                "Открываем...",
                attachment="doc-193964161_629110361",
            )
        await asyncio.sleep(5.8)

        if type == "weapon":
            await self.message.answer(
                f"Выпало оружие {name} ({'★' * rarity})!", attachment=picture
            )
        elif type == "character":
            await self.message.answer(
                f"Выпал персонаж {name} ({'★' * rarity})!", attachment=picture
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
