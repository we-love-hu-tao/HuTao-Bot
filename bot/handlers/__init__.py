from . import (
    admin, banners, buy_fates, casino, characters_actions, daily_reward, fun,
    gacha_history, genshin_info, inventory, invite_help, leave, like_reward,
    minigames, nickname, ping, print_id, profile, promocodes, set_uid, start,
    top, wish
)

labelers = [
    admin.bl, banners.bl, buy_fates.bl, casino.bl, genshin_info.bl,
    nickname.bl, characters_actions.bl, daily_reward.bl,
    ping.bl, fun.bl, gacha_history.bl, inventory.bl,
    invite_help.bl, leave.bl, minigames.bl, like_reward.bl,
    print_id.bl, profile.bl, promocodes.bl, set_uid.bl, start.bl,
    top.bl, wish.bl
]

__all__ = ["labelers"]

