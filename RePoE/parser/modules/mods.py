from PyPoE.poe.constants import MOD_DOMAIN
from RePoE.parser.util import write_json, call_with_default_args
from RePoE.parser import Parser_Module
from PyPoE.poe.file.dat import RelationalReader
from PyPoE.poe.file.file_system import FileSystem
from PyPoE.poe.file.ot import OTFileCache
from PyPoE.poe.file.translations import TranslationFileCache
from PyPoE.poe.file.dat import DatRecord
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Union


def _convert_stats(
    stats: Union[
        List[List[Optional[int]]],
        List[List[Union[DatRecord, int]]],
        List[Union[List[Optional[int]], List[Union[DatRecord, int]]]],
    ]
) -> List[Dict[str, Any]]:
    # 'Stats' is a virtual field that is an array of ['Stat1', ..., 'Stat5'].
    # 'Stat{i}' is a virtual field that is an array of ['StatsKey{i}', 'Stat{i}Min', 'Stat{i}Max']
    r = []
    for stat in stats:
        if isinstance(stat[0], DatRecord):
            r.append({"id": stat[0]["Id"], "min": stat[1], "max": stat[2]})
    return r


def _convert_spawn_weights(spawn_weights: zip) -> List[Dict[str, Any]]:
    # 'SpawnWeight' is a virtual field that is a zipped tuple of
    # ('SpawnWeight_TagsKeys', 'SpawnWeight_Values')
    r = []
    for tag, weight in spawn_weights:
        r.append({"tag": tag["Id"], "weight": weight})
    return r


def _convert_generation_weights(generation_weights: zip) -> List[Dict[str, Any]]:
    # 'GenerationWeight' is a virtual field that is a tuple of
    # ('GenerationWeight_TagsKeys', 'GenerationWeight_Values')
    r = []
    for tag, weight in generation_weights:
        r.append({"tag": tag["Id"], "weight": weight})
    return r


def _convert_buff(buff_definition, buff_value):
    if buff_definition is None:
        return {}
    return {"id": buff_definition["Id"], "range": buff_value}


def _convert_granted_effects(granted_effects_per_level: List[DatRecord]) -> List[Dict[str, Any]]:
    if granted_effects_per_level is None:
        return {}
    # These two identify a row in GrantedEffectsPerLevel.dat64
    return [
        {"granted_effect_id": gepl["GrantedEffect"]["Id"], "level": gepl["Level"]} for gepl in granted_effects_per_level
    ]


def _convert_tags_keys(tags_keys: List[DatRecord]) -> List[str]:
    r = []
    for tag in tags_keys:
        r.append(tag["Id"])
    return r


class mods(Parser_Module):
    @staticmethod
    def write(
        file_system: FileSystem,
        data_path: str,
        relational_reader: RelationalReader,
        translation_file_cache: TranslationFileCache,
        ot_file_cache: OTFileCache,
    ) -> None:
        root = {}
        for mod in relational_reader["Mods.dat64"]:
            domain = MOD_DOMAIN_FIX.get(mod["Id"], mod["Domain"])
            obj = {
                "required_level": mod["Level"],
                "stats": _convert_stats(mod["Stats"]),
                "domain": domain.name.lower(),
                "name": mod["Name"],
                "type": mod["ModTypeKey"]["Name"],
                "generation_type": mod["GenerationType"].name.lower(),
                "groups": [family["Id"] for family in mod["Families"]],
                "spawn_weights": _convert_spawn_weights(mod["SpawnWeight"]),
                "generation_weights": _convert_generation_weights(mod["GenerationWeight"]),
                "grants_effects": _convert_granted_effects(mod["GrantedEffectsPerLevelKeys"]),
                "is_essence_only": mod["IsEssenceOnlyModifier"] > 0,
                "adds_tags": _convert_tags_keys(mod["TagsKeys"]),
                "implicit_tags": _convert_tags_keys(mod["ImplicitTagsKeys"]),
            }
            if mod["Id"] in root:
                print("Duplicate mod id:", mod["Id"])
            else:
                root[mod["Id"]] = obj

        write_json(root, data_path, "mods")


# a few unique item mods have the wrong mod domain so they wouldn't be added to the file without this
MOD_DOMAIN_FIX = {
    "AreaDamageUniqueBodyDexInt1": MOD_DOMAIN.ITEM,
    "ElementalResistancePerEnduranceChargeDescentShield1": MOD_DOMAIN.ITEM,
    "LifeGainOnEndurangeChargeConsumptionUniqueBodyStrInt6": MOD_DOMAIN.ITEM,
    "ReturningProjectilesUniqueDescentBow1": MOD_DOMAIN.ITEM,
}


if __name__ == "__main__":
    call_with_default_args(mods.write)
