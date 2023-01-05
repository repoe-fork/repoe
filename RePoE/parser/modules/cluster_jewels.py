from typing import Any, Dict, List

from PyPoE.poe.file.dat import RelationalReader
from PyPoE.poe.file.file_system import FileSystem
from PyPoE.poe.file.ot import OTFileCache
from PyPoE.poe.file.translations import TranslationFileCache

from RePoE.parser import Parser_Module
from RePoE.parser.util import call_with_default_args, write_json


class cluster_jewels(Parser_Module):
    @staticmethod
    def write(
        file_system: FileSystem,
        data_path: str,
        relational_reader: RelationalReader,
        translation_file_cache: TranslationFileCache,
        ot_file_cache: OTFileCache,
    ) -> None:
        skills: Dict[str, List[Dict[str, Any]]] = {}
        for row in relational_reader["PassiveTreeExpansionSkills.dat64"]:
            size = row["PassiveTreeExpansionJewelSizesKey"]["Name"]
            if size not in skills:
                skills[size] = []
            skills[size].append(
                {
                    "id": row["PassiveSkillsKey"]["Id"],
                    "name": row["PassiveSkillsKey"]["Name"],
                    "stats": {stat["Id"]: value for stat, value in row["PassiveSkillsKey"]["Stats"]},
                    "tag": row["TagsKey"]["Id"],
                }
            )

        data = {}
        for row in relational_reader["PassiveTreeExpansionJewels.dat64"]:
            size = row["PassiveTreeExpansionJewelSizesKey"]["Name"]
            data[row["BaseItemTypesKey"]["Id"]] = {
                "name": row["BaseItemTypesKey"]["Name"],
                "size": size,
                "min_skills": row["MinNodes"],
                "max_skills": row["MaxNodes"],
                "small_indices": row["SmallIndices"],
                "notable_indices": row["NotableIndices"],
                "socket_indices": row["SocketIndices"],
                "total_indices": row["TotalIndices"],
                "passive_skills": skills[size],
            }
        write_json(data, data_path, "cluster_jewels")


if __name__ == "__main__":
    call_with_default_args(cluster_jewels.write)
