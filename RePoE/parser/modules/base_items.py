import os
from collections import defaultdict
from io import BytesIO
from typing import Any, Dict, Optional

from PIL import Image
from PyPoE.poe.constants import MOD_DOMAIN
from PyPoE.poe.file.dat import DatReader, DatRecord, RelationalReader
from PyPoE.poe.file.file_system import FileSystem
from PyPoE.poe.file.ot import OTFileCache
from PyPoE.poe.file.translations import TranslationFileCache

from RePoE.parser import Parser_Module
from RePoE.parser.util import call_with_default_args, get_release_state, write_json


def _create_default_dict(relation: DatReader) -> Dict:
    d = {row["BaseItemTypesKey"]["Id"]: row for row in relation if row["BaseItemTypesKey"] is not None}
    return defaultdict(lambda: None, d)


def _add_if_greater_zero(value: int, key: str, obj: Dict[str, int]) -> None:
    if value > 0:
        obj[key] = value


def _add_if_not_zero(value: int, key: str, obj: Dict[str, Dict[str, int]]) -> None:
    if value != 0:
        obj[key] = value


def _convert_requirements(attribute_requirements: Optional[DatRecord], drop_level: int) -> Optional[Dict[str, int]]:
    if attribute_requirements is None:
        return None
    return {
        "strength": attribute_requirements["ReqStr"],
        "dexterity": attribute_requirements["ReqDex"],
        "intelligence": attribute_requirements["ReqInt"],
        "level": drop_level,
    }


def _convert_armour_properties(armour_row: Optional[DatRecord], properties: Dict) -> None:
    if armour_row is None:
        return
    _add_min_max(armour_row, "Armour", "armour", properties)
    _add_min_max(armour_row, "Evasion", "evasion", properties)
    _add_min_max(armour_row, "EnergyShield", "energy_shield", properties)
    _add_if_not_zero(armour_row["IncreasedMovementSpeed"], "movement_speed", properties)


def _add_min_max(row: DatRecord, row_key_prefix: str, key: str, obj: Dict[str, Dict[str, int]]) -> None:
    if row[row_key_prefix + "Min"] > 0:
        obj[key] = {"min": row[row_key_prefix + "Min"], "max": row[row_key_prefix + "Max"]}


def _convert_shield_properties(shield_row: Optional[DatRecord], properties: Dict[str, Any]) -> None:
    if shield_row is None:
        return
    properties["block"] = shield_row["Block"]


def _convert_flask_properties(flask_row: Optional[DatRecord], properties: Dict[str, Any]) -> None:
    if flask_row is None:
        return
    _add_if_greater_zero(flask_row["LifePerUse"], "life_per_use", properties)
    _add_if_greater_zero(flask_row["ManaPerUse"], "mana_per_use", properties)
    _add_if_greater_zero(flask_row["RecoveryTime"], "duration", properties)


def _convert_flask_buff(flask_row: Optional[DatRecord], item_object: Dict[str, Any]) -> Optional[Any]:
    if flask_row is None or flask_row["BuffDefinitionsKey"] is None:
        return None
    stats_values = zip(flask_row["BuffDefinitionsKey"]["StatsKeys"], flask_row["BuffStatValues"])
    item_object["grants_buff"] = {
        "id": flask_row["BuffDefinitionsKey"]["Id"],
        "stats": {},
    }
    for (stat, value) in stats_values:
        item_object["grants_buff"]["stats"][stat["Id"]] = value


def _convert_flask_charge_properties(flask_row: Optional[DatRecord], properties: Dict[str, Any]) -> None:
    if flask_row is None:
        return
    properties["charges_max"] = flask_row["MaxCharges"]
    properties["charges_per_use"] = flask_row["PerCharge"]


def _convert_weapon_properties(weapon_row: Optional[DatRecord], properties: Dict[str, Any]) -> None:
    if weapon_row is None:
        return
    properties["critical_strike_chance"] = weapon_row["Critical"]
    properties["attack_time"] = weapon_row["Speed"]
    properties["physical_damage_min"] = weapon_row["DamageMin"]
    properties["physical_damage_max"] = weapon_row["DamageMax"]
    properties["range"] = weapon_row["RangeMax"]


def _convert_currency_properties(currency_row: Optional[DatRecord], properties: Dict[str, Any]) -> None:
    if currency_row is None:
        return
    properties["stack_size"] = currency_row["Stacks"]
    properties["directions"] = currency_row["Directions"]
    if currency_row["FullStack_BaseItemTypesKey"]:
        properties["full_stack_turns_into"] = currency_row["FullStack_BaseItemTypesKey"]["Id"]
    properties["description"] = currency_row["Description"]
    properties["stack_size_currency_tab"] = currency_row["CurrencyTab_StackSize"]


ITEM_CLASS_WHITELIST = {
    "LifeFlask",
    "ManaFlask",
    "HybridFlask",
    "Currency",
    "Amulet",
    "Ring",
    "Claw",
    "Dagger",
    "Rune Dagger",
    "Wand",
    "One Hand Sword",
    "Thrusting One Hand Sword",
    "One Hand Axe",
    "One Hand Mace",
    "Bow",
    "Staff",
    "Warstaff",
    "Two Hand Sword",
    "Two Hand Axe",
    "Two Hand Mace",
    "Active Skill Gem",
    "Support Skill Gem",
    "Quiver",
    "Belt",
    "Gloves",
    "Boots",
    "Body Armour",
    "Helmet",
    "Shield",
    "StackableCurrency",
    "Sceptre",
    "UtilityFlask",
    "UtilityFlaskCritical",
    "FishingRod",
    "Jewel",
    "AbyssJewel",
    "DivinationCard",
    "Map",
    "MapFragment",
    "AtlasRegionUpgradeItem",
    "ExpeditionLogbook",
    "IncubatorStackable",
    "AtlasUpgradeItem",
    "SentinelDrone",
    "DelveStackableSocketableCurrency",
    "DelveSocketableCurrency",
    "QuestItem",
    "HeistContract",
    "HeistBlueprint",
    "HeistEquipmentWeapon",
    "HeistEquipmentTool",
    "HeistEquipmentUtility",
    "HeistEquipmentReward",
    "MemoryLine",
    "Relic",
    "SanctumSpecialRelic",
}

ITEM_CLASS_BLACKLIST = {
    "LabyrinthTrinket",
    "MiscMapItem",
    "Leaguestone",
    "LabyrinthItem",
    "PantheonSoul",
    "UniqueFragment",
    "IncursionItem",
    "MetamorphosisDNA",
    "HideoutDoodad",
    "LabyrinthMapItem",
    "Incubator",
    "Microtransaction",
    "HarvestInfrastructure",
    "HarvestSeed",
    "HarvestPlantBooster",
    "Trinket",
    "HeistObjective",
    "HiddenItem",
    "ArchnemesisMod",
}


class base_items(Parser_Module):
    @staticmethod
    def write(
        file_system: FileSystem,
        data_path: str,
        relational_reader: RelationalReader,
        translation_file_cache: TranslationFileCache,
        ot_file_cache: OTFileCache,
    ) -> None:
        attribute_requirements = _create_default_dict(relational_reader["ComponentAttributeRequirements.dat64"])
        armour_types = _create_default_dict(relational_reader["ArmourTypes.dat64"])
        shield_types = _create_default_dict(relational_reader["ShieldTypes.dat64"])
        flask_types = _create_default_dict(relational_reader["Flasks.dat64"])
        flask_charges = _create_default_dict(relational_reader["ComponentCharges.dat64"])
        weapon_types = _create_default_dict(relational_reader["WeaponTypes.dat64"])
        currency_type = _create_default_dict(relational_reader["CurrencyItems.dat64"])
        # Not covered here: SkillGems.dat64 (see gems.py), Essences.dat64 (see essences.py)

        root = {}
        skipped_item_classes = set()
        for item in relational_reader["BaseItemTypes.dat64"]:

            if item["ItemClassesKey"]["Id"] in ITEM_CLASS_BLACKLIST:
                skipped_item_classes.add(item["ItemClassesKey"]["Id"])
                continue
            elif item["ItemClassesKey"]["Id"] in ITEM_CLASS_WHITELIST:
                pass
            else:
                raise ValueError(f"Unknown item class, not in whitelist or blacklist: {item['ItemClassesKey']['Id']}")

            ot_path = item["InheritsFrom"] + ".it"
            inherited_tags = list(ot_file_cache[ot_path]["Base"]["tag"])
            mod_domain = item["ModDomainsKey"]
            item_id = item["Id"]
            properties = {}
            _convert_armour_properties(armour_types[item_id], properties)
            _convert_shield_properties(shield_types[item_id], properties)
            _convert_flask_properties(flask_types[item_id], properties)
            _convert_flask_charge_properties(flask_charges[item_id], properties)
            _convert_weapon_properties(weapon_types[item_id], properties)
            _convert_currency_properties(currency_type[item_id], properties)
            root[item_id] = {
                "name": item["Name"],
                "item_class": item["ItemClassesKey"]["Id"],
                "inventory_width": item["Width"],
                "inventory_height": item["Height"],
                "drop_level": item["DropLevel"],
                "implicits": [mod["Id"] for mod in item["Implicit_ModsKeys"]],
                "tags": [tag["Id"] for tag in item["TagsKeys"]] + inherited_tags,
                "visual_identity": {
                    "id": item["ItemVisualIdentityKey"]["Id"],
                    "dds_file": item["ItemVisualIdentityKey"]["DDSFile"],
                },
                "requirements": _convert_requirements(attribute_requirements[item_id], item["DropLevel"]),
                "properties": properties,
                "release_state": get_release_state(item_id).name,
                "domain": mod_domain.name.lower() if mod_domain is not MOD_DOMAIN.MODS_DISALLOWED else "undefined",
            }
            _convert_flask_buff(flask_types[item_id], root[item_id])

            ddsfile = item["ItemVisualIdentityKey"]["DDSFile"]
            if ddsfile:
                bytes = file_system.extract_dds(file_system.get_file(ddsfile))
                if not bytes:
                    print(f"dds file not found {ddsfile}")
                    continue
                if bytes[:4] != b"DDS ":
                    print(f"{ddsfile} was not a dds file")
                    continue
                dest = os.path.join(data_path, os.path.splitext(ddsfile)[0])
                os.makedirs(os.path.dirname(dest), exist_ok=True)

                with Image.open(BytesIO(bytes)) as image:
                    image.save(dest + ".png")
                    image.save(dest + ".webp")

        print(f"Skipped the following item classes for base_items {skipped_item_classes}")
        write_json(root, data_path, "base_items")


if __name__ == "__main__":
    call_with_default_args(base_items.write)
