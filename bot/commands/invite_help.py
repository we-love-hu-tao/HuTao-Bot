from vkbottle.bot import Blueprint, Message
from variables import HELP_LINK

bp = Blueprint("Invite event")


@bp.on.message(action="chat_invite_user")
async def invite_event_reaction(message: Message):
    if message.action.member_id == -193964161:
        await message.answer(
            "Добро пожаловать в Тейват!\n"
            "Теперь мне необходимо дать права на чтение сообщений "
            "и админку для корректной работы!\n"
            "Статья со всеми командами:\n"
            + HELP_LINK
        )


@bp.on.message(text="!помощь")
async def help_handler(message: Message):
    await message.answer(
        "Основные команыды:\n"
        "!начать - создать профиль\n"
        "!перс - просмотреть персонажа\n"
        "!установить ник [никнейм] - устанавливает ник для вашего персонажа\n"
        "Все остальные команды можно посмотреть в статье:\n"
        + HELP_LINK
    )
