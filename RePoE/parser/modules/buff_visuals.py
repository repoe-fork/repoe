from collections import defaultdict
from functools import cache
import json
import re

from PyPoE.poe.file.dat import DatRecord
from PyPoE.poe.file.idl import IDLFile
from PyPoE.poe.file.translations import TranslationFileCache

from RePoE.parser import Parser_Module
from RePoE.parser.util import call_with_default_args, export_image, write_json

BUFF_SOURCES = [
    {"dat": "BuffDefinitions", "key": "BuffVisualsKey"},
    {"dat": "BuffTemplates", "key": "BuffVisualsKey"},
    {"dat": "ExplodingStormBuffs", "key": "BuffVisualsKey"},
    {"dat": "LegionFactions", "key": "BuffVisualsKey"},
    {"dat": "DroneBaseTypes", "key": "Visual"},
]


class buff_visuals(Parser_Module):
    def write(self) -> None:
        idl = IDLFile()
        idl.read(self.file_system.get_file("Art/UIImages1.txt"))
        self.ui_images = idl.as_dict()
        self.tc: TranslationFileCache = self.get_cache(TranslationFileCache)
        for definition in BUFF_SOURCES:
            self.relational_reader[definition["dat"] + ".dat64"].build_index(definition["key"])

        root = {}

        for record in self.relational_reader["BuffVisuals.dat64"]:
            visuals = {}
            if record["BuffDDSFile"]:
                visuals["icon"] = record["BuffDDSFile"]
                if self.language == "English":
                    export_image(
                        record["BuffDDSFile"],
                        self.data_path,
                        self.file_system,
                    )
            if record["BuffName"]:
                visuals["name"] = record["BuffName"]
            if record["BuffDescription"]:
                visuals["description"] = record["BuffDescription"]
            if record["ExtraArt"]:
                visuals["custom_frame"] = record["ExtraArt"]
                if self.language == "English" and record["ExtraArt"] in self.ui_images:
                    image = self.ui_images[record["ExtraArt"]]
                    export_image(
                        image.source,
                        self.data_path,
                        self.file_system,
                        image.destination,
                        (image.x1, image.y1, image.x2 + 1, image.y2 + 1),
                    )

            sources = defaultdict(list)
            for definition in BUFF_SOURCES:
                for row in self.relational_reader[definition["dat"] + ".dat64"].index[definition["key"]][record]:
                    source = self.source(row)
                    sources[definition["dat"]].append(source)
            if "name" not in visuals:
                source = [source for sourcetype in sources.values() for source in sourcetype if "name" in source]
                if len(source) == 1:
                    visuals["name"] = source[0].pop("name")
            if "description" not in visuals:
                source = [source for sourcetype in sources.values() for source in sourcetype if "description" in source]
                if len(source) == 1:
                    visuals["description"] = source[0].pop("description")

            if sources:
                visuals["sources"] = sources

            sounds = set()
            for epkfile in record["EPKFiles1"] + record["EPKFiles2"]:
                sounds.update(self.epkfile(epkfile))

            if sounds:
                visuals["sounds"] = list(sounds)

            root[record["Id"]] = visuals

        write_json(root, self.data_path, "buff_visuals")

    @cache
    def epkfile(self, epkfile):
        result = []
        try:
            raw = self.file_system.get_file(epkfile)
            epk = raw.decode("utf-16_le")
            for aofile in re.findall(r'"([^"]*.ao)"', epk):
                result.extend(self.aofile(aofile))
        except FileNotFoundError:
            print(epkfile, "not found")
        except UnicodeDecodeError:
            print(f"{epkfile} (length {len(raw)}) not valid utf-16")
        return result

    @cache
    def aofile(self, aofile):
        result = []
        try:
            raw = self.file_system.get_file(aofile + "c")
            aoc = raw.decode("utf-16_le")
            for data in re.findall(r"SoundEvents\s*{\s*animations\s*=\s*'([^']*)'", aoc):
                for animation in json.loads(data):
                    for event in animation.get("events", []):
                        if "filename" in event:
                            result.append(event["filename"])
        except FileNotFoundError:
            print(aofile + "c", "not found")
        except UnicodeDecodeError:
            print(f"{aofile}c (length {len(raw)}) not valid utf-16")
        return result

    def source(self, row: DatRecord):
        result = {}
        if "Id" in row.parent.columns_all:
            result["id"] = row["Id"]
        if "BaseType" in row.parent.columns_all:
            result["item"] = row["BaseType"]["Id"]
        if "Name" in row.parent.columns_all and row["Name"]:
            result["name"] = row["Name"]
        if "Description" in row.parent.columns_all and row["Description"]:
            result["description"] = row["Description"]
        return result


if __name__ == "__main__":
    call_with_default_args(buff_visuals)
