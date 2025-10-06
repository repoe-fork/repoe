from collections import defaultdict

from PyPoE.poe import poe1constants
from PyPoE.poe.file.dat import DatRecord
from PyPoE.poe.file.idl import IDLFile
from PyPoE.poe.file.translations import TranslationFileCache
from PyPoE.poe.sim.mods import get_translation_file_from_domain

from RePoE.parser import Parser_Module
from RePoE.parser.util import call_with_default_args, write_json

BUFF_CATEGORIES = {
    1: "Buff",
    2: "Debuff",
    3: "Charge",
    4: "Flask",
    5: "Hex",
    6: "Active skill",
    7: "Buff shrine",
    8: "PVP flag",
    9: "Spell shrine",
    10: "PVP team",
    11: "Labyrinth trap",
    12: "Aspect",
    13: "Herald",
    14: "Mark",
    15: "Stolen",
    16: "Link",
    17: "Tincture",
    # some rows have category value greater than the number of rows in BuffCategories.dat (e.g. grace_period)
    # the category value of those rows appears to increase as new buff categories are added,
    # so it's safer not to hard-code that number, and count all unknown category values as uncategorized.
}

BUFF_SOURCES = [
    {"dat": "LabyrinthSecretEffects", "key": "Buff_BuffDefinitionsKey", "values": "Buff_StatValues"},
    {"dat": "LabyrinthTrinkets", "key": "Buff_BuffDefinitionsKey", "values": "Buff_StatValues"},
    {"dat": "BlightedSporeAuras", "key": "BuffDefinitionsKey", "values": "BuffStatValues"},
    {"dat": "BlightTowerAuras", "key": "BuffDefinitionsKey"},
    {"dat": "RitualRuneTypes", "key": "BuffDefinitionsKey", "values": "BuffStatValues"},
    {"dat": "CorpseTypeTags", "key": "RavenousBuff"},
    {
        "dat": "ExplodingStormBuffs",
        "key": "BuffDefinitionsKey1",
        "values": "StatValues",
        "stat_file": "map_stat_descriptions.txt",
    },
    {"dat": "ExplodingStormBuffs", "key": "BuffDefinitionsKey2", "stat_file": "map_stat_descriptions.txt"},
    {"dat": "Flasks", "key": "BuffDefinitionsKey", "values": "BuffStatValues"},
    {"dat": "PlayerConditions", "key": "BuffDefinitionsKeys"},
]

BUFF_TEMPLATE_SOURCES = [
    {"dat": "Mods", "key": "BuffTemplate", "is_array": False},
    {"dat": "PassiveSkills", "key": "PassiveSkillBuffs", "is_array": True},
    {"dat": "UltimatumModifiers", "key": "BuffTemplates", "is_array": True},
]


class buffs(Parser_Module):
    def write(self) -> None:
        idl = IDLFile()
        idl.read(self.file_system.get_file("Art/UIImages1.txt"))
        self.ui_images = idl.as_dict()
        self.tc: TranslationFileCache = self.get_cache(TranslationFileCache)
        for source in BUFF_SOURCES:
            self.relational_reader[source["dat"] + ".dat64"].build_index(source["key"])
        self.relational_reader["BuffTemplates.dat64"].build_index("BuffDefinitionsKey")
        self.relational_reader["Mods.dat64"].build_index("BuffTemplate")
        self.relational_reader["PassiveSkills.dat64"].build_index("PassiveSkillBuffs")
        self.relational_reader["UltimatumModifiers.dat64"].build_index("BuffTemplates")

        root = {}

        for record in self.relational_reader["BuffDefinitions.dat64"]:
            buff = {key.lower(): record[key] for key in ["Name", "Description", "Invisible", "Removable"]}
            buff["visuals"] = record["BuffVisualsKey"]["Id"]
            if record["BuffLimit"]:
                buff["stack_limit"] = record["BuffLimit"]
            if record["BuffCategory"] in BUFF_CATEGORIES:
                buff["category"] = BUFF_CATEGORIES[record["BuffCategory"]]
            stats = [s["Id"] for s in record["StatsKeys"]] + [s["Id"] for s in record["Binary_StatsKeys"]]
            buff["stats"] = stats

            sources = defaultdict(list)
            templates = {}
            for source in BUFF_SOURCES:
                for row in self.relational_reader[source["dat"] + ".dat64"].index[source["key"]][record]:
                    result = self.source(source, row, record, stats)
                    if result:
                        sources[source["dat"]].append(result)

            for row in self.relational_reader["BuffTemplates.dat64"].index["BuffDefinitionsKey"][record]:
                stat_file = "stat_descriptions.txt"
                for source in self.relational_reader["Mods.dat64"].index["BuffTemplate"][row]:
                    sources["Mods"].append({"id": source["Id"], "template": row["Id"]})
                    stat_file = get_translation_file_from_domain(source["Domain"], poe1constants)
                for source in self.relational_reader["PassiveSkills.dat64"].index["PassiveSkillBuffs"][row]:
                    sources["PassiveSkills"].append({"id": source["Id"], "template": row["Id"]})
                    stat_file = "passive_skill_aura_stat_descriptions.txt"
                for source in self.relational_reader["UltimatumModifiers.dat64"].index["BuffTemplates"][row]:
                    sources["UltimatumModifiers"].append({"id": source["Id"], "template": row["Id"]})
                template = self.source(
                    {
                        "dat": "BuffTemplates",
                        "key": "BuffDefinitionsKey",
                        "values": "Buff_StatValues",
                        "stat_file": stat_file,
                    },
                    row,
                    record,
                    stats,
                )
                if row["AuraRadius"]:
                    template["aura_radius_metres"] = row["AuraRadius"] / 10
                if row["BuffVisualsKey"]:
                    template["visuals"] = row["BuffVisualsKey"]["Id"]
                templates[template.pop("id")] = template

            if sources:
                buff["sources"] = sources
            if templates:
                buff["templates"] = templates

            root[record["Id"]] = buff

        write_json(root, self.data_path, "buffs")

    def source(self, definition: dict, row: DatRecord, buff: DatRecord, stat_ids: list[str]):
        result = {}
        if "Id" in row.parent.columns_all:
            result["id"] = str(row["Id"])
        if "BaseItemTypesKey" in row.parent.columns_all:
            result["item"] = row["BaseItemTypesKey"]["Id"]
        if "Name" in row.parent.columns_all:
            result["name"] = row["Name"]
        if stat_ids:
            if "values" in definition:
                values = row[definition["values"]] + [1 for _ in buff["Binary_StatsKeys"]]
                use_placeholder = False
            else:
                values = [1 for _ in stat_ids]
                use_placeholder = True
            result["stats"] = dict(zip(stat_ids, values))
            tr = self.tc[definition.get("stat_file", "stat_descriptions.txt")].get_translation(
                stat_ids, values, full_result=True, lang=self.language, use_placeholder=use_placeholder
            )
            if tr.lines:
                result["stat_text"] = tr.lines
        return result


if __name__ == "__main__":
    call_with_default_args(buffs)
