from vkbottle.bot import Blueprint, Message
from vkbottle import PhotoMessageUploader
from player_exists import HasAccount
import aiosqlite

bp = Blueprint("Profile")
bp.labeler.vbml_ignore_case = True


@bp.on.message(HasAccount(), text=("!персонаж", "!перс"))
async def profile(message: Message):
    async with aiosqlite.connect("db.db") as db:
        async with db.execute(
            "SELECT "
            "nickname, "
            "standard_wishes, "
            "event_wishes, "
            "legendary_rolls_standard, "
            "legendary_rolls_event "
            "FROM players WHERE user_id=(?)",
            (message.from_id,),
        ) as cur:
            result = await cur.fetchone()

    nickname = result[0]
    standard_wishes = result[1]
    event_wishes = result[2]
    legendary_standard_guarantee = result[3]
    legendary_event_guarantee = result[4]

    await message.answer(
        f"Ник: {nickname}\nСтандартных молитв: {standard_wishes}\nМолитв "
        f"события: {event_wishes}\n\nОткрытых стандартных молитв без 5 "
        f"звездочного предмета: {legendary_standard_guarantee}\n\nОткрытых "
        " ивентовых молитв без 5 звездочного предмета:"
        f"{legendary_event_guarantee}"
    )


@bp.on.message(HasAccount(), text=("!установить фото", "!поставить фото"))
async def set_image(message: Message):
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
            await message.answer("image", attachment=photo_link)
        else:
            print("not image")
    else:
        await message.answer("Вы не прикрепили картинку!")
