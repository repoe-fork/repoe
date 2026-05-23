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
                mods_by_domain.setdefault(mod["domain"], {})[mod_id] = mod

        for base_id, base in base_items.items():
            item_class: dict = item_classes[base["item_class"]]
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
                for mod_id, mod in mods_by_domain.get(base["domain"], {}).items():
                    weight = next((weight["weight"] for weight in mod["spawn_weights"] if weight["tag"] in tags), None)
                    conditional_weight = next(
                        (weight["weight"] for weight in mod["spawn_weights"] if weight["tag"] in conditional_tags), None
                    )
                    if weight != conditional_weight:
                        conditional_mods.add(mod_id)
                    if not weight and not conditional_weight:
                        continue
                    mod_generation = mods_data.root.setdefault(mod["generation_type"], ModTypes({}))
                    mod_group = mod_generation.root.setdefault(mod["type"], ModWeights({}))
                    mod_group.root[mod_id] = mod["required_level"]
                    for added_tag in mod.get("adds_tags", []):
                        if added_tag not in conditional_tags:
                            restart = conditional_tags[added_tag] = True
                            conditional_tags.move_to_end(added_tag, False)
                    if restart:
                        break
            if conditional_mods:
                by_tags.conditional_mods = list(sorted(conditional_mods))

        # clean up
        # for class_name, class_val in list(root.root.items()):
        #     for tags, tag_set in list(class_val.root.items()):
        #         print(tags, tag_set)
        #         if not tag_set.mods.root:
        #             del class_val.root[tags]
        #     if not class_val.root:
        #         del root.root[class_name]

        write_json(root, self.data_path, "mods_by_base")


if __name__ == "__main__":
    call_with_default_args(mods_by_base)
