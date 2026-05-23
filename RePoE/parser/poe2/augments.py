from collections import OrderedDict

from PyPoE.poe.file.translations import TranslationFileCache

from RePoE.parser import Parser_Module
from RePoE.parser.util import call_with_default_args, write_any_json


class augments(Parser_Module):
    def write(self) -> None:
        root = {}
        relational_reader = self.relational_reader
        translation_cache = self.get_cache(TranslationFileCache)
        trans_file = translation_cache["stat_descriptions.txt"]

        soul_cores = relational_reader["SoulCores.dat64"]
        soul_core_stats = relational_reader["SoulCoreStats.dat64"]
        if "SoulCore" not in soul_core_stats.index:
            soul_core_stats.build_index("SoulCore")

        for soul_core in soul_cores:
            base_item_type = soul_core["BaseItemType"]
            if base_item_type is None:
                continue

            obj = {}

            if soul_core["RequiredLevel"]:
                obj["required_level"] = soul_core["RequiredLevel"]
            if soul_core["Type"]:
                obj["type_id"] = soul_core["Type"]["Id"]
                obj["type_name"] = soul_core["Type"]["Name"]
            if soul_core["Limit"]:
                limit_text = soul_core["Limit"]["Text"]
                limit_val = soul_core["Limit"]["Limit"]
                if limit_text:
                    obj["limit"] = limit_text.format(limit_val)
                else:
                    obj["limit"] = str(limit_val)

            categories = {}
            obj["categories"] = categories

            for sc_stat in soul_core_stats.index["SoulCore"].get(soul_core, []):
                results = {}
                categories[sc_stat["StatCategory"]["Id"]] = results
                if sc_stat["StatCategory"]["Display"]:
                    results["target"] = sc_stat["StatCategory"]["Display"]
                else:
                    results["target"] = list(map(lambda c: c["Name"], sc_stat["StatCategory"]["TargetItemClasses"]))

                if sc_stat["Stats"]:
                    stats = []
                    stat_ids = []
                    for s in sc_stat["Stats"]:
                        stats.append({"id": s["Id"], "local": s["IsLocal"]})
                        stat_ids.append(s["Id"])
                    results["stats"] = stats
                    result = trans_file.get_translation(stat_ids, sc_stat["StatsValues"], lang=self.language)
                    if hasattr(result, "lines"):
                        lines = result.lines
                    else:
                        lines = result
                    if lines:
                        results["stat_text"] = lines

                if sc_stat["BondedStats"]:
                    stats = []
                    stat_ids = []
                    for s in sc_stat["BondedStats"]:
                        stats.append({"id": s["Id"], "local": s["IsLocal"]})
                        stat_ids.append(s["Id"])
                    results["bonded_stats"] = stats
                    result = trans_file.get_translation(stat_ids, sc_stat["BondedStatsValues"], lang=self.language)
                    if hasattr(result, "lines"):
                        lines = result.lines
                    else:
                        lines = result
                    if lines:
                        results["bonded_stat_text"] = lines

            root[base_item_type["Id"]] = obj

        write_any_json(root, self.data_path, "augments")


if __name__ == "__main__":
    call_with_default_args(augments)
