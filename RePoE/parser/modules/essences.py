from RePoE.parser import Parser_Module
from RePoE.parser.util import call_with_default_args, write_json
from PyPoE.poe.file.dat import DatRecord
from typing import Dict


def _convert_mods(row: DatRecord) -> Dict[str, str]:
    class_to_key = {
        "Amulet": "Amulet_ModsKey",
        "Belt": "Belt_ModsKey",
        "Body Armour": "BodyArmour_ModsKey",
        "Boots": "Boots_ModsKey",
        "Bow": "Bow_ModsKey",
        "Claw": "Claw_ModsKey",
        "Dagger": "Dagger_ModsKey",
        "Gloves": "Gloves_ModsKey",
        "Helmet": "Helmet_ModsKey",
        "One Hand Axe": "OneHandAxe_ModsKey",
        "One Hand Mace": "OneHandMace_ModsKey",
        "One Hand Sword": "OneHandSword_ModsKey",
        "Quiver": "Display_Quiver_ModsKey",
        "Ring": "Ring_ModsKey",
        "Sceptre": "Sceptre_ModsKey",
        "Shield": "Shield_ModsKey",
        "Staff": "Staff_ModsKey",
        "Thrusting One Hand Sword": "OneHandThrustingSword_ModsKey",
        "Two Hand Axe": "TwoHandAxe_ModsKey",
        "Two Hand Mace": "TwoHandMace_ModsKey",
        "Two Hand Sword": "TwoHandSword_ModsKey",
        "Wand": "Wand_ModsKey",
    }
    return {item_class: row[key]["Id"] for item_class, key in class_to_key.items() if row[key] is not None}


class essences(Parser_Module):
    def write(self) -> None:
        essences = {
            row["BaseItemTypesKey"]["Id"]: {
                "name": row["BaseItemTypesKey"]["Name"],
                "spawn_level_min": row["DropLevelMinimum"],
                "spawn_level_max": row["DropLevelMaximum"],
                "level": row["Level"],
                "item_level_restriction": row["ItemLevelRestriction"] if row["ItemLevelRestriction"] > 0 else None,
                "type": {
                    "tier": row["EssenceTypeKey"]["EssenceType"],
                    "is_corruption_only": row["EssenceTypeKey"]["IsCorruptedEssence"],
                },
                "mods": _convert_mods(row),
            }
            for row in self.relational_reader["Essences.dat64"]
        }
        write_json(essences, self.data_path, "essences")


if __name__ == "__main__":
    call_with_default_args(essences)
