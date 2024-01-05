import subprocess
import sys

import msgspec
from utils import translate
from vkbottle.bot import BotLabeler, Message

bl = BotLabeler()
bl.vbml_ignore_case = True


def get_battery_status() -> dict | str:
    try:
        battery_info_raw = subprocess.check_output(
            "termux-battery-status", shell=True
        ).decode("utf-8")
    except subprocess.CalledProcessError as e:
        return e
    battery_info = msgspec.json.decode(battery_info_raw)
    return battery_info


@bl.message(text=("!пинг", "!гнш пинг"))
async def do_ping(_: Message):
    text = await translate("ping", "pong")

    if not hasattr(sys, 'getandroidapilevel'):
        return text
    battery_status = get_battery_status()
    if type(battery_status) is str:
        text += f"\n\nНе удалось получить заряд батери телефона: {battery_status}"
        return text

    battery_percentage = battery_status["percentage"]
    charging = battery_status["status"]
    plugged_text = ("(заряжается)" if charging == "CHARGING" else "")
    text += f"\n\n🔋 Заряд батареи: {battery_percentage}% {plugged_text}" + (
        " (зарядите скорее!)" if battery_percentage < 20 else ""
    )

    return text
