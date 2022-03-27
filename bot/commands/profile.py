from vkbottle.bot import Blueprint, Message
from player_exists import exists
import aiosqlite

bp = Blueprint("Profile")
bp.labeler.vbml_ignore_case = True


@bp.on.message(text=("!персонаж", "!перс"))
async def profile(message: Message):
    if not await exists(message):
        return
    async with aiosqlite.connect("db.db") as db:
        async with db.execute(
            "SELECT "
            "nickname, "
            "photo_link, "
            "standard_wishes, "
            "event_wishes, "
            "legendary_rolls_standard, "
            "legendary_rolls_event "
            "FROM players WHERE user_id=(?)",
            (message.from_id,),
        ) as cur:
            result = await cur.fetchone()

    nickname = result[0]
    photo_link = result[1]
    standard_wishes = result[2]
    event_wishes = result[3]
    legendary_standard_guarantee = result[4]
    legendary_event_guarantee = result[5]

    await message.answer(
        f"Ник: {nickname}\nСтандартных молитв: {standard_wishes}\nМолитв "
        f"события: {event_wishes}\n\nОткрытых стандартных молитв без 5 "
        f"звездочного предмета: {legendary_standard_guarantee}\n\nОткрытых "
        " ивентовых молитв без 5 звездочного предмета:"
        f"{legendary_event_guarantee}",
        attachment=photo_link
    )


@bp.on.message(text=("!установить фото", "!поставить фото"))
async def set_image(message: Message):
    if not await exists(message):
        return
    if message.attachments:
        if message.attachments[0].photo:
            photo = message.attachments[0].photo
            photo_link = "photo" + str(photo.owner_id) + "_" + str(photo.id)
            async with aiosqlite.connect("db.db") as db:
                await db.execute(
                    "UPDATE players SET photo_link=(?) WHERE user_id=(?)",
                    (photo_link, message.from_id),
                )
                await db.commit()
            print("sending")
            await message.answer("Готово!")
        else:
            print("not image")
    else:
        await message.answer("Вы не прикрепили картинку!")
