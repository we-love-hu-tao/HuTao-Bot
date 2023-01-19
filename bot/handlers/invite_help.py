from vkbottle.bot import BotLabeler, Message

from config import GROUP_ID

bl = BotLabeler()
bl.vbml_ignore_case = True

HELP_LINK = "https://github.com/timius100/HuTao-Bot#команды"


@bl.message(action="chat_invite_user")
async def invite_event_reaction(message: Message):
    """React when bot is invited to a chat"""
    if message.action.member_id == -GROUP_ID:
        return (
            "Добро пожаловать в Тейват!\n"
            "Теперь мне необходимо дать права на чтение сообщений "
            "и админку для корректной работы!\n"
            "Репозиторий со всеми командами:\n"
            + HELP_LINK
        )


@bl.message(text="!помощь")
async def help_handler(message: Message):
    await message.answer(
        "Основные команыды:\n"
        "!начать - создать профиль\n"
        "!перс - просмотреть персонажа\n"
        "!установить ник [никнейм] - устанавливает ник для вашего персонажа\n"
        "Все остальные команды можно посмотреть в репозитории:\n"
        + HELP_LINK,
        attachment="photo-193964161_457239344"
    )
