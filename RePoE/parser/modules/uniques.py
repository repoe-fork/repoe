from RePoE.parser import Parser_Module
from RePoE.parser.util import call_with_default_args, export_image, write_json

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


def get_wiki_data():
    offset = 0
    # data will be truncated if it's too large, reducing page size can resolve unterminated json errors
    page_size = 200
    data = []
    while True:
        url = f"https://www.poewiki.net/w/api.php?action=cargoquery&tables=items&where=rarity=%22Unique%22&fields={','.join( fields)}&limit={page_size}&offset={offset}&format=json"
        json = requests.get(url).json()
        if not "cargoquery" in json:
            print(offset, json)
            return data
        page = json["cargoquery"]
        data.extend(page)
        offset += page_size
        if len(page) < page_size:
            result = {}
            for entry in data:
                item = entry["title"]
                name = item["name"]
                if name not in result:
                    result[name] = [item]
                else:
                    result[name].append(item)
            return result


class uniques(Parser_Module):
    def write(self) -> None:
        root = {}
        for item in self.relational_reader["UniqueStashLayout.dat64"]:
            name = item["WordsKey"]["Text"]
            root[item.rowid] = {
                "name": name,
                "item_class": item["UniqueStashTypesKey"]["Id"],
                "inventory_width": item[5] or item["UniqueStashTypesKey"]["Width"],
                "inventory_height": item[6] or item["UniqueStashTypesKey"]["Height"],
                "is_alternate_art": item["IsAlternateArt"],
                "renamed_version": item["RenamedVersion"]
                and {
                    "rowid": item["RenamedVersion"].rowid,
                    "name": item["RenamedVersion"]["WordsKey"]["Text"],
                },
                "base_version": item["BaseVersion"]
                and {"rowid": item["BaseVersion"].rowid, "name": item["BaseVersion"]["WordsKey"]["Text"]},
                "visual_identity": {
                    "id": item["ItemVisualIdentityKey"]["Id"],
                    "dds_file": item["ItemVisualIdentityKey"]["DDSFile"],
                },
            }

            if item["ItemVisualIdentityKey"]["DDSFile"]:
                export_image(item["ItemVisualIdentityKey"]["DDSFile"], self.data_path, self.file_system)

        write_json(root, self.data_path, "uniques")
        write_json(get_wiki_data(), self.data_path, "uniques_poewiki")


if __name__ == "__main__":
    call_with_default_args(uniques)
