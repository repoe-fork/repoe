from PyPoE.poe.file.dat import RelationalReader
from PyPoE.poe.file.file_system import FileSystem
from PyPoE.poe.file.ot import OTFileCache
from PyPoE.poe.file.translations import TranslationFileCache

from RePoE.parser import Parser_Module
from RePoE.parser.util import call_with_default_args, export_image, write_json


class uniques(Parser_Module):
    @staticmethod
    def write(
        file_system: FileSystem,
        data_path: str,
        relational_reader: RelationalReader,
        translation_file_cache: TranslationFileCache,
        ot_file_cache: OTFileCache,
    ) -> None:
        root = {}
        for item in relational_reader["UniqueStashLayout.dat64"]:

            root[item.rowid] = {
                "name": item["WordsKey"]["Text"],
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
                export_image(item["ItemVisualIdentityKey"]["DDSFile"], data_path, file_system)

        write_json(root, data_path, "uniques")


if __name__ == "__main__":
    call_with_default_args(uniques.write)
