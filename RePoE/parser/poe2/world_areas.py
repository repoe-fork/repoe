from PyPoE.poe.file.dat import DatRecord
from PyPoE.poe.file.dgr import DGRFile
from PyPoE.poe.file.file_set import FileSet
from PyPoE.poe.file.tsi import TSIFile

from RePoE.parser import Parser_Module
from RePoE.parser.util import call_with_default_args, write_any_json, write_json

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
        self.graphs = {}
        self.cache = {}

    def write(self) -> None:
        self.packs.build_index("WorldAreas")
        self.pack_entries.build_index("MonsterPacksKey")

        root = {
            area["Id"]: self.process_row(area)
            for area in self.relational_reader["WorldAreas.dat64"]
        }
        write_json(root, self.data_path, "world_areas")
        if self.language == "English":
            for k, v in self.graphs.items():
                write_any_json(v, self.data_path, k)

    def process_row(self, row: DatRecord):
        result = {key: self.process_value(row[pascal_case(key)]) for key in AREA_KEYS}
        if row in self.packs.index["WorldAreas"]:
            result["packs"] = [self.process_pack(p) for p in self.packs.index["WorldAreas"][row]]
        if row["Topologies"]:
            result["topologies"] = [self.process_layout(l) for l in row["Topologies"]]

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
        result["boss_chance"] = pack["BossMonsterSpawnChance"]
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

    def process_layout(self, row: DatRecord):
        dgr_file = row["DGRFile"]
        self.process_graph(dgr_file)

        return {
            "id": row["Id"],
            "file": dgr_file,
            "unknown": [
                row[f] for f in row.parent.specification.fields.keys()
                if f not in ["Id", "DGRFile"]
            ],
        }

    def process_graph(self, filename):
        if filename in self.graphs:
            return
        try:
            file = DGRFile()
            file.read(self.file_system.get_file(filename))
            val = vars(file)
            if "MasterFile" in file.data:
                master = self.process_master(file.data["MasterFile"])
                if master:
                    val["master"] = master
                    base = file.data["MasterFile"]
                    base = base[:base.rfind('/') + 1]
                    if "RoomSet" in master:
                        val["room_set"] = self.process_fileset(base + master["RoomSet"])
                    if "TileSet" in master:
                        val["tile_set"] = self.process_fileset(base + master["TileSet"])
            if "edges" in val:
                val["edge_types"] = {}
                for edge in val["edges"]:
                    [edge_type, color, etfile] = self.process_edge_type(next(
                        u for u in edge["unknown"] if isinstance(u, str) and u.endswith(".et")))
                    val["edge_types"][edge_type] = etfile
                    edge["edge_type"] = edge_type
                    if color:
                        edge["color"] = color
                self.graphs[filename] = val
        except FileNotFoundError:
            print("Graph not found", filename)
        except Exception:
            print("Error in topology", filename)
            raise

    def process_master(self, filename: str):
        if filename in self.cache:
            return self.cache[filename]
        try:
            file = TSIFile()
            file.read(self.file_system.get_file(filename))
            self.cache[filename] = file.data
            return file.data
        except FileNotFoundError:
            print("File not found", filename)
            self.cache[filename] = None
        except Exception:
            print("Error parsing file", filename)
            raise

    def process_fileset(self, filename: str):
        if filename in self.cache:
            return self.cache[filename]
        file = FileSet()
        try:
            file.read(self.file_system.get_file(filename))
            self.cache[filename] = file.files
            return file.files
        except FileNotFoundError:
            print("File not found", filename)
            self.cache[filename] = None
        except Exception:
            print("Error parsing file", filename, file)
            raise

    def process_edge_type(self, filename: str):
        if filename not in self.cache:
            self.cache[filename] = self.file_system.get_file(filename).decode("utf-16")
        etfile: str = self.cache[filename]
        first_line = etfile.splitlines()[0].split()
        match len(first_line):
            case 1:
                return first_line[0], None, etfile
            case 2:
                if not first_line[1].startswith("#"):
                    print("bad color", first_line[1], "in", filename)
                    raise Exception(first_line[1])
                return first_line[0], first_line[1], etfile
            case _:
                raise Exception(filename)


if __name__ == "__main__":
    call_with_default_args(world_areas)
