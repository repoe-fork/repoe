from RePoE.parser.util import write_json, call_with_default_args
from RePoE.parser import Parser_Module
from PyPoE.poe.file.dat import DatRecord
from typing import Dict, Set
from typing import Optional


def _convert_alias_stats(
    alias_stats_key_1: Optional[DatRecord], alias_stats_key_2: Optional[DatRecord]
) -> Dict[str, str]:
    r = {}
    if alias_stats_key_1 is not None:
        r["when_in_main_hand"] = alias_stats_key_1["Id"]
    if alias_stats_key_2 is not None:
        r["when_in_off_hand"] = alias_stats_key_2["Id"]
    return r


class stats(Parser_Module):
    def write(self) -> None:
        root = {}
        previous: Set[str] = set()
        for stat in self.relational_reader["Stats.dat64"]:
            if stat["Id"] in previous:
                print("Duplicate stat id %s" % stat["Id"])
                continue
            root[stat["Id"]] = {
                "is_local": stat["IsLocal"],
                "is_aliased": stat["IsWeaponLocal"],
                "alias": _convert_alias_stats(stat["MainHandAlias_StatsKey"], stat["OffHandAlias_StatsKey"]),
                # 'is_on_character_panel': stat['Flag6'],  # not sure
                # 'is_on_tooltip': stat['Flag7'],  # not sure
            }

        write_json(root, self.data_path, "stats")


if __name__ == "__main__":
    call_with_default_args(stats)
