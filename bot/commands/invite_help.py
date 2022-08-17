from vkbottle.bot import Blueprint, Message
from variables import HELP_LINK, GROUP_ID

bp = Blueprint("Invite event")
bp.labeler.vbml_ignore_case = True


@bp.on.message(action="chat_invite_user")
async def invite_event_reaction(message: Message):
    if message.action.member_id != -GROUP_ID:
        return (
            "Добро пожаловать в Тейват!\n"
            "Теперь мне необходимо дать права на чтение сообщений "
            "и админку для корректной работы!\n"
            "Статья со всеми командами:\n"
            + HELP_LINK
        )


@bp.on.message(text="!помощь")
async def help_handler(message: Message):
    return (
        "Основные команыды:\n"
        "!начать - создать профиль\n"
        "!перс - просмотреть персонажа\n"
        "!установить ник [никнейм] - устанавливает ник для вашего персонажа\n"
        "Все остальные команды можно посмотреть в статье:\n"
        + HELP_LINK
    )


@bp.on.private_message(text="Начать")
async def start_private_handler(message: Message):
    return (
        "Что бы я начал работать, меня надо добавить в любую беседу, и выдать "
        "там доступ к переписке!\n"
        "Команды можно посмотреть тут:\n"
        + HELP_LINK
    )
