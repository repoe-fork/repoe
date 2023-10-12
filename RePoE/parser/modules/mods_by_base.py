import json
from collections import OrderedDict

import requests


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
            mods = json.load(f)
            mods_by_domain: dict[str, dict[str, dict]] = {}
            for mod_id, mod in mods.items():
                if mod["generation_type"] in ["blight_tower", "unique", "tempest", "enchantment", "crucible_tree"]:
                    continue
                mods_by_domain.setdefault(mod["domain"], {})[mod_id] = mod

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
                for domain in [base["domain"], "delve"]:
                    for mod_id, mod in mods_by_domain.get(domain, {}).items():
                        delve = domain == "delve"

                        weight = next(
                            (weight["weight"] for weight in mod["spawn_weights"] if weight["tag"] in tags), None
                        )
                        gen_type = mod["generation_type"]
                        if delve:
                            gen_type = "delve_" + gen_type
                        if not weight:
                            influence = next(
                                (weight for weight in mod["spawn_weights"] if weight["tag"] in influence_tags), {}
                            )
                            if influence:
                                weight = influence["weight"]
                                gen_type = gen_type + "_" + influence["tag"].split("_")[-1]
                            else:
                                continue
                        mod_generation: dict = mods_data.setdefault(gen_type, {})
                        mod_group: dict = mod_generation.setdefault(mod["type"], {})
                        mod_group[mod_id] = weight
                        for added_tag in mod.get("adds_tags", []):
                            if added_tag not in tags:
                                restart = tags[added_tag] = True
                                tags.move_to_end(added_tag, False)
                        if restart:
                            break

        for synth in requests.get(
            "https://www.poewiki.net/index.php?title=Special:CargoExport&tables=synthesis_mods&format=json"
            "&fields=synthesis_mods.item_class_ids__full%3Ditem_classes%2C+synthesis_mods.mod_ids__full%3Dmods"
            "&group+by=synthesis_mods.mod_ids__full%2Csynthesis_mods.item_class_ids__full&order+by=&limit=2000"
        ).json():
            for item_class in synth["item_classes"]:
                results: dict[str, dict] = root[item_classes[item_class]["name"]].setdefault("synthesis", {})
                for mod_id in synth["mods"]:
                    if mod_id == "SynthesisImplicitMaximumAttackDodge1":
                        mod_id = "SynthesisImplicitSpellDamageSuppressed1_"
                    mod = mods[mod_id]
                    group = results.setdefault(mod["type"], [])
                    if mod_id not in group:
                        group.append(mod_id)

        essences = self.relational_reader["Essences.dat64"]
        keys = [k for k in essences.table_columns.keys() if k.endswith("ModsKey") and not k.startswith("Display")]
        item_class_map = {k.replace(" ", "") + "_ModsKey": k for k in item_classes}
        item_class_map["OneHandThrustingSword_ModsKey"] = "Thrusting One Hand Sword"
        for essence in essences:
            name = essence["BaseItemTypesKey"]["Name"]
            if name == "Remnant of Corruption":
                continue
            level = name.split()[0]
            type = name.split()[-1]
            for key in keys:
                result = root[item_classes[item_class_map[key]]["name"]].setdefault("essences", {})
                result.setdefault(type, {})[level] = essence[key]["Id"]

        write_json(root, self.data_path, "mods_by_base")


if __name__ == "__main__":
    call_with_default_args(mods_by_base)
