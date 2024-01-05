import enum
import msgspec


class WeaponType(enum.Enum):
    SWORD = "Sword"
    CLAYMORE = "Claymore"
    POLE = "Pole"
    CATALYST = "Catalyst"
    BOW = "Bow"
    FISHING_ROD = "FishingRod"


class Weapon(msgspec.Struct):
    """Type that describes weapon from `WeaponData.json`"""
    id: int
    weapon_type: WeaponType
    rank: int
    name_text_map_hash: int
    desc_text_map_hash: int
    weapon_name: str
    gacha_img: str
