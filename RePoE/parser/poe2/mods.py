from typing import Any, Dict, List, Optional, Union

from PyPoE.poe.constants import IntEnumOverride
from PyPoE.poe.file.dat import DatRecord
from PyPoE.poe.file.translations import install_data_dependant_quantifiers, TranslationFileCache
from PyPoE.poe.sim.mods import get_translation

from RePoE.parser import Parser_Module
from RePoE.parser.util import call_with_default_args, write_json


class MOD_DOMAIN(IntEnumOverride):
    ITEM = 1
    FLASK = 2
    MONSTER = 3
    CHEST = 4
    STRONGBOX = 5
    AREA = 6
    UNKNOWN1 = 7
    TEMPLAR_RELIC = 8
    UNKNOWN3 = 9
    CRAFTED = 10
    # Corruptions, item limits, jewel mods, other stuff?
    MISC = 11
    ATLAS = 12
    LEAGUESTONE = 13
    ABYSS_JEWEL = 14
    MAP_DEVICE = 15
    DUMMY = 16
    DELVE = 17
    DELVE_AREA = 18
    SYNTHESIS_A = 19
    SYNTHESIS_GLOBALS = 20
    SYNTHESIS_BONUS = 21
    AFFLICTION_JEWEL = 22
    HEIST_AREA = 23
    HEIST_NPC = 24
    HEIST_TRINKET = 25
    WATCHSTONE = 26
    VEILED = 27
    EXPEDITION_RELIC = 28
    UNVEILED = 29
    SENTINEL = 31
    MEMORY_LINES = 32
    SANCTUM_RELIC = 33
    TOWER = 34
    ULTIMATUM = 35

    # Items that can't have mods (may need to increase the number when new values are added)
    MODS_DISALLOWED = 36


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
        {"granted_effect_id": gepl["GrantedEffect"]["Id"], "level": gepl["Level"]} for gepl in
        granted_effects_per_level
    ]


def _convert_tags_keys(tags_keys: List[DatRecord]) -> List[str]:
    r = []
    for tag in tags_keys:
        r.append(tag["Id"])
    return r


class mods(Parser_Module):
    def write(self) -> None:
        root = {}
        translation_cache = self.get_cache(TranslationFileCache)
        install_data_dependant_quantifiers(self.relational_reader)
        prices = self.relational_reader["GoldModPrices.dat64"]
        prices.build_index("Mod")
        for mod in self.relational_reader["Mods.dat64"]:
            domain = MOD_DOMAIN_FIX.get(mod["Id"], mod["Domain"])
            price = prices.index["Mod"][mod]
            if isinstance(price, list):
                price = next(iter(price), None)

            try:
                lines = get_translation(mod, translation_cache, lang=self.language).lines
            except Exception as e:
                print("could not get text for mod", mod["Id"], e)
                lines = []

            obj = {
                "required_level": mod["Level"],
                "stats": _convert_stats(mod["Stats"]),
                "text": "\n".join(lines) if lines else None,
                "domain": domain.name.lower(),
                "name": mod["Name"],
                "type": mod["ModType"]["Name"],
                "generation_type": mod["GenerationType"].name.lower() if mod[
                    "GenerationType"] else "<unknown>",
                "groups": [family["Id"] for family in mod["Families"]],
                "spawn_weights": _convert_spawn_weights(
                    zip(price["Tags"], price["SpawnWeight"])) if price else [],
                "generation_weights": _convert_generation_weights(mod["GenerationWeight"]),
                "grants_effects": _convert_granted_effects(mod["GrantedEffectsPerLevel"]),
                "is_essence_only": mod["IsEssenceOnlyModifier"] > 0,
                "adds_tags": _convert_tags_keys(mod["Tags"]),
                "implicit_tags": _convert_tags_keys(mod["ImplicitTags"]),
                "gold_value": price["Value"] if price else None
            }
            if mod["Id"] in root:
                print("Duplicate mod id:", mod["Id"])
            else:
                root[mod["Id"]] = obj

        write_json(root, self.data_path, "mods")


# a few unique item mods have the wrong mod domain so they wouldn't be added to the file without this
MOD_DOMAIN_FIX = {
    "AreaDamageUniqueBodyDexInt1": MOD_DOMAIN.ITEM,
    "ElementalResistancePerEnduranceChargeDescentShield1": MOD_DOMAIN.ITEM,
    "LifeGainOnEndurangeChargeConsumptionUniqueBodyStrInt6": MOD_DOMAIN.ITEM,
    "ReturningProjectilesUniqueDescentBow1": MOD_DOMAIN.ITEM,
}

if __name__ == "__main__":
    call_with_default_args(mods)
