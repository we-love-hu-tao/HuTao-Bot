from vkbottle.bot import Blueprint, Message
from variables import EVENT_BANNER

bp = Blueprint("Banners command")
bp.labeler.vbml_ignore_case = True


EVENT_BANNERS = {
    "moment_of_bloom": "photo-193964161_457239044",
    "dance_of_lanterns": "photo-193964161_457239049",
    "drifting_luminescence": "photo-193964161_457239096",
    "everbloom_violet": "photo-193964161_457239017",
    "reign_of_serenity": "photo-193964161_457239095",
    "emergency_food": "photo-193964161_457239220",
    "sparkling_steps": "photo-193964161_457239257"
}


@bp.on.message(command="ив баннер")
async def show_event_banner(message: Message):
    await message.answer(attachment=EVENT_BANNERS[EVENT_BANNER])


@bp.on.message(command="ст баннер")
async def show_standard_banner(message: Message):
    await message.answer(attachment="photo-193964161_457239097")
