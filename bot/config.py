import os

from dotenv import load_dotenv

load_dotenv()

# ! Do not change anything in this file.
# ! Use .env for configuring the bot.

try:
    VK_GROUP_TOKEN = os.getenv("VK_GROUP_TOKEN")
    GROUP_ID = int(os.getenv("GROUP_ID"))

    VK_USER_TOKEN = os.getenv("VK_USER_TOKEN")

    # Removing empty string elements and converting them to int
    ADMIN_IDS = tuple(int(i) for i in os.getenv("ADMIN_IDS").split(",") if i)

    BANNERS_ALBUM_ID = int(os.getenv("BANNERS_ALBUM_ID"))
    CURRENT_LANG = os.getenv("LANG")
except ValueError as e:
    raise ValueError(f"Empty or invalid variables in .env: {e}")
