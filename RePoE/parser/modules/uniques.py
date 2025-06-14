from html import escape
from time import sleep
from urllib.parse import quote
from RePoE.parser import Parser_Module
from RePoE.parser.util import call_with_default_args, export_image, write_json, write_text

import requests

fields = [
    field if "=" in field else f"{field}={field}"
    for field in [
        "_pageName=page_name",
        "acquisition_tags",
        "base_item",
        "base_item_id",
        "cannot_be_traded_or_modified",
        "class=item_class",
        "class_id=item_class_id",
        "description",
        "drop_areas",
        "drop_enabled",
        "drop_level",
        "drop_monsters",
        "drop_text",
        "influences",
        "is_account_bound",
        "is_corrupted",
        "is_drop_restricted",
        "is_eater_of_worlds_item",
        "is_fractured",
        "is_in_game",
        "is_relic",
        "is_replica",
        "is_searing_exarch_item",
        "is_synthesised",
        "is_unmodifiable",
        "is_veiled",
        "name",
        "name_list",
        "release_version",
        "removal_version",
        "required_dexterity",
        "required_intelligence",
        "required_strength",
        "required_level",
        "tags",
    ]
]


class uniques(Parser_Module):
    def write(self) -> None:
        root = {}
        html = (
            """<!DOCTYPE html>
<html>
<head>
 <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
 <title>"""
            + escape(
                self.relational_reader["ClientStrings.dat64"].index["Id"]["TutorialPanelRarityTiersSubtitle1"]["Text"]
            )
            + """</title>
 <style type="text/css">
  BODY { font-family : monospace, sans-serif;  color: black;}
  A:visited { text-decoration : none; margin : 0px; padding : 0px;}
  A:link    { text-decoration : none; margin : 0px; padding : 0px;}
  A:hover   { text-decoration: underline; background-color : yellow; margin : 0px; padding : 0px;}
  A:active  { margin : 0px; padding : 0px;}
 </style>
</head>
<body>"""
        )
        all_items = self.relational_reader["UniqueStashLayout.dat64"]
        for item in all_items:
            name = item["WordsKey"]["Text2"]

            # Some alt arts don't provide override-width/-height
            # https://github.com/repoe-fork/repoe/issues/30
            override = (
                item
                if item["OverrideWidth"] and item["OverrideHeight"]
                else next(
                    (
                        i
                        for i in all_items
                        if i["WordsKey"] == item["WordsKey"] and i["OverrideWidth"] and i["OverrideHeight"]
                    ),
                    None,
                )
            )

            root[str(item.rowid)] = {
                "id": item["WordsKey"]["Text"],
                "name": name,
                "item_class": item["UniqueStashTypesKey"]["Id"],
                "inventory_width": override["OverrideWidth"] if override else item["UniqueStashTypesKey"]["Width"],
                "inventory_height": override["OverrideHeight"] if override else item["UniqueStashTypesKey"]["Height"],
                "is_alternate_art": item["IsAlternateArt"],
                "renamed_version": item["RenamedVersion"]
                and {
                    "rowid": item["RenamedVersion"].rowid,
                    "name": item["RenamedVersion"]["WordsKey"]["Text2"],
                },
                "base_version": item["BaseVersion"]
                and {"rowid": item["BaseVersion"].rowid, "name": item["BaseVersion"]["WordsKey"]["Text2"]},
                "visual_identity": {
                    "id": item["ItemVisualIdentityKey"]["Id"],
                    "dds_file": item["ItemVisualIdentityKey"]["DDSFile"],
                },
            }

            if item["ItemVisualIdentityKey"]["DDSFile"]:
                ddsfile: str = item["ItemVisualIdentityKey"]["DDSFile"]
                name = escape(name) + (" (Alternate Art)" if item["IsAlternateArt"] else "")
                href = ("" if self.language == "English" else "../") + ddsfile.replace(".dds", ".png")
                html = html + f"\n\t<a href='{quote(href)}'>{name}</a><br>"
                if self.language == "English":
                    export_image(ddsfile, self.data_path, self.file_system)

        html = (
            html
            + """
</body>
</html>
"""
        )

        write_json(root, self.data_path, "uniques")
        write_text(html, self.data_path, "uniques.html")


if __name__ == "__main__":
    call_with_default_args(uniques)
