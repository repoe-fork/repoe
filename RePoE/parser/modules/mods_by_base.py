import json
from collections import OrderedDict

import requests

from RePoE.model.mods_by_base import (
    EssenceModLevels,
    EssenceMods,
    ItemClasses,
    ModTypes,
    ModWeights,
    SynthModGroups,
    TagSet,
    TagSets,
)
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
        root = ItemClasses({})

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
            by_class = root.root.setdefault(item_class["name"], TagSets({}))
            by_tags: TagSet = by_class.root.setdefault(",".join(base["tags"]), TagSet(bases=[], mods={}))
            by_tags.bases.append(base_id)
            mods_data = by_tags.mods
            tags = OrderedDict.fromkeys(base["tags"])
            conditional_tags = OrderedDict(tags)
            conditional_mods = set()
            restart = True
            while restart:
                restart = False
                for domain in [base["domain"], "delve"]:
                    for mod_id, mod in mods_by_domain.get(domain, {}).items():
                        delve = domain == "delve"

                        weight = next(
                            (weight["weight"] for weight in mod["spawn_weights"] if weight["tag"] in tags), None
                        )
                        conditional_weight = next(
                            (weight["weight"] for weight in mod["spawn_weights"] if weight["tag"] in conditional_tags),
                            None,
                        )
                        if weight != conditional_weight:
                            conditional_mods.add(mod_id)
                        gen_type = mod["generation_type"]
                        if delve:
                            gen_type = "delve_" + gen_type
                        if not weight and not conditional_weight:
                            influence = next(
                                (weight for weight in mod["spawn_weights"] if weight["tag"] in influence_tags), {}
                            )
                            if influence:
                                weight = influence["weight"]
                                gen_type = gen_type + "_" + influence["tag"].split("_")[-1]
                            else:
                                continue
                        mod_generation = mods_data.root.setdefault(gen_type, ModTypes({}))
                        mod_group = mod_generation.root.setdefault(mod["type"], ModWeights({}))
                        mod_group.root[mod_id] = weight
                        for added_tag in mod.get("adds_tags", []):
                            if added_tag not in conditional_tags:
                                restart = conditional_tags[added_tag] = True
                                conditional_tags.move_to_end(added_tag, False)
                        if restart:
                            break
            if conditional_mods:
                by_tags.conditional_mods = list(sorted(conditional_mods))

        for synth in requests.get(
            "https://www.poewiki.net/index.php?title=Special:CargoExport&tables=synthesis_mods&format=json"
            "&fields=synthesis_mods.item_class_ids__full%3Ditem_classes%2C+synthesis_mods.mod_ids__full%3Dmods"
            "&group+by=synthesis_mods.mod_ids__full%2Csynthesis_mods.item_class_ids__full&order+by=&limit=2000"
        ).json():
            for item_class in synth["item_classes"]:
                results: SynthModGroups = root.root[item_classes[item_class]["name"]].root.setdefault(
                    "synthesis", SynthModGroups({})
                )
                for mod_id in synth["mods"]:
                    if mod_id == "SynthesisImplicitMaximumAttackDodge1":
                        mod_id = "SynthesisImplicitSpellDamageSuppressed1_"
                    mod = mods[mod_id]
                    group = results.root.setdefault(mod["type"], [])
                    if mod_id not in group:
                        group.append(mod_id)

        essences = self.relational_reader["Essences.dat64"]
        keys = [k for k in essences.table_columns.keys() if k.endswith("ModsKey") and not k.startswith("Display")]
        item_class_map = {k.replace(" ", "") + "_ModsKey": k for k in item_classes}
        item_class_map["OneHandThrustingSword_ModsKey"] = "Thrusting One Hand Sword"
        for essence in essences:
            essence_item = essence["BaseItemTypesKey"]
            if essence_item["Id"] == "Metadata/Items/Currency/CurrencyCorruptMonolith":
                continue
            name = essence_item["Name"]
            level = name.split()[0]
            type = name.split()[-1]
            for key in keys:
                essence_levels: EssenceModLevels = root.root[item_classes[item_class_map[key]]["name"]].root.setdefault(
                    "essences", EssenceModLevels({})
                )
                essence_levels.root.setdefault(type, EssenceMods({})).root[level] = essence[key]["Id"]

        write_json(root, self.data_path, "mods_by_base")


if __name__ == "__main__":
    call_with_default_args(mods_by_base)
