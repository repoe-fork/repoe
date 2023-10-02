import io
import json
import os
import traceback
from hashlib import md5
from io import BytesIO
from typing import Any, Optional

from PIL import Image
from PyPoE.poe.file.dat import RelationalReader
from PyPoE.poe.file.file_system import FileSystem
from PyPoE.poe.file.specification.data import generated

from RePoE import __DATA_PATH__
from RePoE.parser import Parser_Module
from RePoE.parser.constants import (
    LEGACY_ITEMS,
    STAT_DESCRIPTION_NAMING_EXCEPTIONS,
    UNIQUE_ONLY_ITEMS,
    UNRELEASED_ITEMS,
    ReleaseState,
)


def get_id_or_none(relational_file_cell):
    return None if relational_file_cell is None else relational_file_cell["Id"]


def write_json(
    root_obj: Any,
    data_path: str,
    file_name: str,
) -> None:
    print("Writing '" + str(file_name) + ".json' ...", end="", flush=True)
    json.dump(root_obj, io.open(data_path + file_name + ".json", mode="w"), indent=2, sort_keys=True)
    print(" Done!")
    print("Writing '" + str(file_name) + ".min.json' ...", end="", flush=True)
    json.dump(root_obj, io.open(data_path + file_name + ".min.json", mode="w"), separators=(",", ":"), sort_keys=True)
    print(" Done!")


def write_text(
    text: str,
    data_path: str,
    file_name: str,
) -> None:
    print("Writing '" + str(file_name) + "' ...", end="", flush=True)
    with io.open(data_path + file_name, mode="w") as out:
        out.write(text)
    print(" Done!")


def load_file_system(ggpk_path: str) -> FileSystem:
    return FileSystem(ggpk_path)


def create_relational_reader(file_system: FileSystem) -> RelationalReader:
    opt = {
        "use_dat_value": False,
        "auto_build_index": True,
        "x64": True,
    }
    return RelationalReader(
        path_or_file_system=file_system, files=["Stats.dat64"], specification=generated.specification, read_options=opt
    )


DEFAULT_GGPK_PATH = "C:/Program Files (x86)/Grinding Gear Games/Path of Exile"


def call_with_default_args(module: type[Parser_Module]):
    file_system = load_file_system(DEFAULT_GGPK_PATH)
    return module(
        file_system=file_system, data_path=__DATA_PATH__, relational_reader=create_relational_reader(file_system)
    ).write()


def get_release_state(item_id: str) -> ReleaseState:
    if item_id in UNRELEASED_ITEMS:
        return ReleaseState.unreleased
    if item_id in LEGACY_ITEMS:
        return ReleaseState.legacy
    if item_id in UNIQUE_ONLY_ITEMS:
        return ReleaseState.unique_only
    return ReleaseState.released


def get_stat_translation_file_name(game_file: str) -> Optional[str]:
    if game_file in STAT_DESCRIPTION_NAMING_EXCEPTIONS:
        return f"stat_translations{STAT_DESCRIPTION_NAMING_EXCEPTIONS[game_file]}"
    elif game_file.endswith("_stat_descriptions.txt"):
        suffix_length = len("_stat_descriptions.txt")
        return f"stat_translations/{game_file[:-suffix_length]}"
    elif game_file.endswith("descriptions.txt"):
        raise ValueError(
            f"The following stat description file name is not accounted for: {game_file},"
            + " please add it to STAT_DESCRIPTION_NAMING_EXCEPTIONS in constants.py or add a generalized case to"
            + " util.py::get_stat_translation_file_name"
        )
    else:
        return None


def export_image(ddsfile: str, data_path: str, file_system: FileSystem) -> None:
    try:
        bytes = file_system.extract_dds(file_system.get_file(ddsfile))
    except Exception:
        print(f"Failed to extract {ddsfile}")
        traceback.print_exc()
        return
    if not bytes:
        print(f"dds file not found {ddsfile}")
        return
    if bytes[:4] != b"DDS ":
        print(f"{ddsfile} was not a dds file")
        return
    dest = os.path.join(data_path, os.path.splitext(ddsfile)[0])
    os.makedirs(os.path.dirname(dest), exist_ok=True)

    # output images can vary slightly for the same input;
    # hash the input data to avoid committing unnecessary changes
    hashfile = dest + ".dds.md5sum"
    exists = os.path.isfile(hashfile) and os.path.isfile(dest + ".png") and os.path.isfile(dest + ".webp")
    with open(hashfile, "r+" if os.path.isfile(hashfile) else "w") as f:
        hash = md5(bytes).hexdigest()
        if exists and hash == f.read():
            return
        else:
            f.seek(0)
            f.write(hash)
            f.truncate()

    with Image.open(BytesIO(bytes)) as image:
        image.save(dest + ".png")
        image.save(dest + ".webp")
