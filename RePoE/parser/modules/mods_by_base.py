import json
from collections import OrderedDict


from RePoE.parser import Parser_Module
from RePoE.parser.util import call_with_default_args, write_json

include_classes = set(
    [
        "AbyssJewel",
        "ExpeditionLogbook",
        "FishingRod",
        "HeistBlueprint",
        "HeistContract",
        "HeistEquipmentReward",
        "HeistEquipmentTool",
        "HeistEquipmentUtility",
        "HeistEquipmentWeapon",
        "Flask",
        "Jewel",
        "Map",
        "Relic",
        "Trinket",
    ]
)


class mods_by_base(Parser_Module):
    def write(self) -> None:
        root = {}

        with open(self.data_path + "base_items.min.json") as f:
            base_items: dict[str, dict] = json.load(f)
        with open(self.data_path + "item_classes.min.json") as f:
            item_classes: dict = json.load(f)
        with open(self.data_path + "mods.min.json") as f:
            mods: dict[str, dict[str, dict]] = {}
            for mod_id, mod in json.load(f).items():
                if mod["generation_type"] in ["blight_tower", "unique", "tempest", "enchantment", "crucible_tree"]:
                    continue
                mods.setdefault(mod["domain"], {})[mod_id] = mod

        for base_id, base in base_items.items():
            item_class: dict = item_classes[base["item_class"]]
            influence_tags = item_class.get("influence_tags", [])
            if not (influence_tags or item_class.get("category_id", None) in include_classes):
                continue
            by_class: dict = root.setdefault(item_class["name"], {})
            by_tags: dict = by_class.setdefault(",".join(base["tags"]), {})
            by_tags.setdefault("bases", []).append(base_id)
            mods_data: dict = by_tags.setdefault("mods", {})
            tags = OrderedDict.fromkeys(base["tags"])
            restart = True
            while restart:
                restart = False
                for mod_id, mod in mods.get(base["domain"], {}).items():
                    weight = next((weight["weight"] for weight in mod["spawn_weights"] if weight["tag"] in tags), 0)
                    type = mod["generation_type"]
                    if not weight:
                        influence = next(
                            (weight for weight in mod["spawn_weights"] if weight["tag"] in influence_tags), {}
                        )
                        if influence:
                            weight = influence["weight"]
                            type = type + "_" + influence["tag"].split("_")[-1]
                        else:
                            continue
                    mod_generation: dict = mods_data.setdefault(type, {})
                    mod_group: dict = mod_generation.setdefault(mod["type"], {})
                    mod_group[mod_id] = weight
                    for added_tag in mod.get("adds_tags", []):
                        if added_tag not in tags:
                            restart = tags[added_tag] = True
                            tags.move_to_end(added_tag, False)
                    if restart:
                        break

        write_json(root, self.data_path, "mods_by_base")


if __name__ == "__main__":
    call_with_default_args(mods_by_base)
