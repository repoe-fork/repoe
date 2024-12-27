from collections import defaultdict
from functools import cache
import html
import json
from os import path
import re

from PyPoE.poe.file.dat import DatRecord
from PyPoE.poe.file.idl import IDLFile
from PyPoE.poe.file.translations import TranslationFileCache

from RePoE.parser import Parser_Module
from RePoE.parser.modules.buffs import BUFF_CATEGORIES
from RePoE.parser.util import call_with_default_args, export_image, write_json, write_text, crop

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
        self.img_path = "" if self.language == "English" else "../"

        root = {}
        by_icon = defaultdict(list)
        id_by_icon = defaultdict(list)

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
                        compose=crop(image.x1, image.y1, image.x2 + 1, image.y2 + 1),
                    )

            sources = defaultdict(list)
            for definition in BUFF_SOURCES:
                for row in self.relational_reader[definition["dat"] + ".dat64"].index[definition["key"]][record]:
                    source = self.source(row)
                    sources[definition["dat"]].append(source)

            if sources:
                visuals["sources"] = sources

            sounds = set()
            for epkfile in record["EPKFiles1"] + record["EPKFiles2"]:
                sounds.update(self.epkfile(epkfile))

            if sounds:
                visuals["sounds"] = sorted(sounds)

            root[record["Id"]] = visuals
            if "icon" in visuals:
                by_icon[visuals["icon"]].append(visuals)
                id_by_icon[visuals["icon"]].append(record["Id"])

        write_json(root, self.data_path, "buff_visuals")
        write_text(
            f"""<!DOCTYPE html>
<html>
<head>
 <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
 <title>status effects ({self.language})</title>
 <style type="text/css">
  BODY {{ font-family : monospace, sans-serif;  color: black;}}
  IMG {{ max-width: 64px; max-height: 64px;}}
 </style>
</head>
<body>
{"".join(f'''
  <div id="{html.escape(icon)}">
    <h3>{html.escape(' / '.join(sorted(set([buff["name"] for buff in buffs if "name" in buff] or [
        source["name"]
        for buff in buffs
        for sources in buff.get("sources", {}).values()
        for source in sources
        if "name" in source
    ]))))}</h3>
    <img src="{self.img_path}{html.escape(path.splitext(icon)[0])}.png" alt="status icon">
    <details>
      <summary>Details
        <button onclick="openAll()">Show all</button>
        <button onclick="closeAll()">Hide all</button>
      </summary>
      <p>BuffVisuals id(s): {", ".join(id_by_icon[icon])}</p>
      <ul>{"".join(self.html(buff) for buff in buffs)}</ul>
    </details>
  </div>''' for icon, buffs in by_icon.items())}
<script>
function openAll() {{
  document.querySelectorAll('details').forEach(e => e.setAttribute('open', true));
}}
function closeAll() {{
  document.querySelectorAll('details').forEach(e => e.removeAttribute('open'));
}}
if (window.location.hash) {{
  document.getElementById(window.location.hash.substring(1))?.querySelector('details')?.setAttribute('open', true);
}}
</script>
</body>
</html>""",
            self.data_path,
            "buff_visuals.html",
        )
        write_text(
            f"""<!DOCTYPE html>
<html>
<head>
 <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
 <title>status effects ({self.language})</title>
 <style type="text/css">
  BODY {{ font-family : monospace, sans-serif;  color: black;}}
  IMG {{ max-width: 64px; max-height: 64px; padding: 0 2px;}}
  DIV {{ float: left;}}
 </style>
</head>
<body>
{"".join(f'''
  <div>
    <a href="buff_visuals.html#{html.escape(icon)}">
        <img src="{self.img_path}{html.escape(path.splitext(icon)[0])}.png" alt="status icon" title="{
            html.escape(' / '.join(sorted(set([buff["name"] for buff in buffs if "name" in buff] or [
                source["name"]
                for buff in buffs
                for sources in buff.get("sources", {}).values()
                for source in sources
                if "name" in source
            ]))))}">
    </a>
  </div>''' for icon, buffs in by_icon.items())}
</body>
</html>""",
            self.data_path,
            "buff_visuals_grid.html",
        )

    def html(self, buff, type=""):
        return (
            (
                f"""
        <li>
          <h4>{html.escape(buff["name"])}{f" ({buff['buff_category']})" if "buff_category" in buff else ""}</h4>
          {f"<p>{html.escape(buff['description'])}</p>" if "description" in buff else ""}
          {f"<p>{type} id: {buff['id']}" if "id" in buff else ""}
          {f"<p>buff id: {buff['buff_id']}" if "buff_id" in buff else ""}
        </li>
"""
                if "name" in buff
                else ""
            )
            + "".join(self.html(buff, k) for k, buffs in buff.get("sources", {}).items() for buff in buffs)
        )

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

        for col in ["BuffDefinitionsKey", "BuffDefinitionsKey1", "BuffDefinitionsKey2"]:
            if col in row.parent.columns_all and row[col]:
                buff = row[col]
                result["buff_id"] = buff["Id"]
                if buff["BuffCategory"] in BUFF_CATEGORIES:
                    result["buff_category"] = BUFF_CATEGORIES[buff["BuffCategory"]]
                if buff["Name"]:
                    result["name"] = buff["Name"]
                if buff["Description"]:
                    result["description"] = buff["Description"]
                break

        if "Name" in row.parent.columns_all and row["Name"]:
            result["name"] = row["Name"]
        if "Description" in row.parent.columns_all and row["Description"]:
            result["description"] = row["Description"]
        if "BuffCategory" in row.parent.columns_all and row["BuffCategory"] in BUFF_CATEGORIES:
            result["buff_category"] = BUFF_CATEGORIES[row["BuffCategory"]]

        return result


if __name__ == "__main__":
    call_with_default_args(buff_visuals)
