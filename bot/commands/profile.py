from vkbottle.bot import Blueprint, Message
from vkbottle import PhotoMessageUploader
from player_exists import HasAccount
import aiosqlite

bp = Blueprint('Profile')
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
            "FROM players WHERE user_id=(?)", (message.from_id,)
        ) as cur:
            result = await cur.fetchone()

    nickname = result[0]
    standard_wishes = result[1]
    event_wishes = result[2]
    legendary_standard_guarantee = result[3]
    legendary_event_guarantee = result[4]

    await message.answer(
        f"Ник: {nickname}\n"
        f"Стандартных молитв: {standard_wishes}\n"
        f"Молитв события: {event_wishes}\n\n"
        f"Открытых стандартных молитв без 5 звездочного предмета: {legendary_standard_guarantee}\n\n"
        f"Открытых ивентовых молитв без 5 звездочного предмета: {legendary_event_guarantee}"
    )


@bp.on.message(HasAccount(), text=("!установить фото", "!поставить фото"))
async def set_image(message: Message):
    if message.attachments:
        if message.attachments[0].photo:
            photo = message.attachments[0].photo
            sizes = photo.sizes
            for size in sizes:
                if size.type.value == "x":
                    best_size = size
                    break
            print(f"best size: {best_size}")
            async with aiosqlite.connect("db.db") as db:
                await db.execute("UPDATE players SET photo_link=(?) WHERE user_id=(?)", (best_size.url, message.from_id))
                await db.commit()
            print("sending")
            await message.answer("image", attachment=best_size.url)  # ! вместо картинки прикладывает ссылку на неё
        else:
            print("not image")
    else:
        await message.answer("Вы не прикрепили картинку!")
    