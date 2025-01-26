from PyPoE.poe.file.dat import DatRecord, RelationalReader
from PyPoE.poe.file.file_system import FileSystem
from PyPoE.poe.file.shared.cache import AbstractFileCache

from RePoE.parser import Parser_Module
from RePoE.parser.util import call_with_default_args, write_any_json

AREA_KEYS = [
    "id", "name", "act", "is_town", "has_waypoint", "connections", "area_level", "loading_screens",
    "parent_town", "bosses", "area_mods", "tags", "environment", "terrain_plugins",
]

PACK_KEYS = [
    "id", "min_count", "max_count", "boss_monster_spawn_chance", "boss_count", "boss_monsters",
    "formation", "tags"
]


def pascal_case(key: str):
    return ''.join(word.title() for word in key.split('_'))


class world_areas(Parser_Module):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.packs = self.relational_reader["MonsterPacks.dat64"]
        self.pack_entries = self.relational_reader["MonsterPackEntries.dat64"]

    def write(self) -> None:
        self.packs.build_index("WorldAreas")
        self.pack_entries.build_index("MonsterPacksKey")

        root = [self.process_row(area) for area in self.relational_reader["WorldAreas.dat64"]]
        write_any_json(root, self.data_path, "world_areas")

    def process_row(self, row: DatRecord):
        result = {key: self.process_value(row[pascal_case(key)]) for key in AREA_KEYS}
        if row in self.packs.index["WorldAreas"]:
            result["packs"] = [self.process_pack(p) for p in self.packs.index["WorldAreas"][row]]
        return result

    def process_value(self, val):
        if isinstance(val, DatRecord):
            return val["Id"]
        elif isinstance(val, list):
            return [self.process_value(v) for v in val]
        else:
            return val

    def process_pack(self, pack: DatRecord):
        result = {key: self.process_value(pack[pascal_case(key)]) for key in PACK_KEYS}
        if pack in self.pack_entries.index["MonsterPacksKey"]:
            result["monsters"] = {
                p["MonsterVarietiesKey"]["Id"]: {
                    "weight": p["Weight"],
                    "flag": p["Flag"],
                } for p in self.pack_entries.index["MonsterPacksKey"][pack]
            }
        if pack["AdditionalMonsters"]:
            result["additional_monsters"] = {
                monster["Id"]: {"count": count}
                for monster, count in zip(pack["AdditionalMonsters"], pack["AdditionalCounts"])
            }
        return result


if __name__ == "__main__":
    call_with_default_args(world_areas)
