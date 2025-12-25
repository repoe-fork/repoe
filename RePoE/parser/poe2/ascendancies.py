import os.path

from PyPoE.cli.exporter.wiki.parsers.passives import CLASS_PASSIVES
from PyPoE.poe.file.psg import PSGFile, GraphGroup, GraphGroupNode
from PyPoE.poe.file.translations import TranslationFileCache

from RePoE.parser import Parser_Module
from RePoE.parser.modules.flavour import flavour
from RePoE.parser.poe2.passives import uiart, passive
from RePoE.parser.util import call_with_default_args, write_any_json

COLS = {
    "ClassNo": "class_number",
    "Character": "character",
    "CoordinateRect": "coordinate_rect",
    "Name": "name",
    "FlavourText": "flavour_text",
    "RGBFlavourTextColour": "flavour_text_colour",
    "OGGFile": "string",
    "PassiveTreeImage": "passive_tree_image",
    "TreeRegionVector": "tree_region_vector",
    "TreeRegionAngle": "tree_region_angle",
    "Disabled": "disabled",
    "BaseAscendancy": "overrides_ascendancy",
}


class ascendancies(Parser_Module):

    def write(self) -> None:
        self.relational_reader["AscendancyPassiveSkillOverrides.dat64"].build_index("AscendancyToOverrideFor")
        write_any_json(
            {asc["Id"]: self.process(asc) for asc in self.relational_reader["Ascendancy.dat64"]},
            self.data_path,
            "ascendancies",
        )

    def process(self, row):
        tf = self.get_cache(TranslationFileCache)["passive_skill_stat_descriptions.txt"]

        data = {v: row[k] for k, v in COLS.items()}
        data["art"] = uiart(row["UIArt"])
        if row["BaseAscendancy"]:
            data["passive_overrides"] = [
                {
                    "from_hash": o["SkillToOverride"]["PassiveSkillGraphId"],
                    "to_passive": passive(o["Override"], tf, self.language),
                }
                for o in self.relational_reader["AscendancyPassiveSkillOverrides.dat64"].index[
                    "AscendancyToOverrideFor"
                ][row]
            ]
        return data


if __name__ == "__main__":
    call_with_default_args(ascendancies)
