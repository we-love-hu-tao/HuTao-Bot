from typing import List, Optional

import msgspec


class ProfilePicture(msgspec.Struct, rename="camel"):
    avatar_id: int
    costume_id: Optional[int] = None


class ShowAvatarInfoList(msgspec.Struct, rename="camel"):
    avatar_id: int
    level: int
    costume_id: Optional[int] = None


class PlayerInfo(msgspec.Struct, rename="camel"):
    nickname: str
    level: int
    signature: Optional[str] = None
    world_level: Optional[int] = None
    profile_picture: Optional[ProfilePicture] = None
    show_avatar_info_list: Optional[List[ShowAvatarInfoList]] = None


class PlayerProfile(msgspec.Struct, rename="camel"):
    """Type that describes player profile from enka.network"""
    player_info: PlayerInfo
