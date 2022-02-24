from vkbottle.bot import Blueprint, Message

bp = Blueprint("Banners command")
bp.labeler.vbml_ignore_case = True


@bp.on.message(command="ив баннер")
async def show_event_banner(message: Message):
    await message.answer(attachment="photo-193964161_457239017")


@bp.on.message(command="ст баннер")
async def show_standard_banner(message: Message):
    await message.answer(attachment="photo-193964161_457239020")
