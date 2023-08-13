import argparse

import RePoE
from RePoE import __DATA_PATH__
from importlib import reload

from RePoE.parser.modules import get_parser_modules

from RePoE.parser.util import (
    create_relational_reader,
    create_translation_file_cache,
    DEFAULT_GGPK_PATH,
    create_ot_file_cache,
    load_file_system,
)


def main():

    modules = get_parser_modules()

    module_names = [module.__name__ for module in modules]
    module_names.append("all")
    parser = argparse.ArgumentParser(description="Convert GGPK files to Json using PyPoE")
    parser.add_argument(
        "module_names",
        metavar="module",
        nargs="+",
        choices=module_names,
        help="the converter modules to run (choose from '" + "', '".join(module_names) + "')",
    )
    parser.add_argument("-f", "--file", default=DEFAULT_GGPK_PATH, help="path to your Content.ggpk file")
    args = parser.parse_args()

    print("Loading GGPK ...", end="", flush=True)
    file_system = load_file_system(args.file)
    print(" Done!")

    selected_module_names = args.module_names
    if "all" in selected_module_names:
        selected_module_names = [m for m in module_names if m != "all"]

    rr = create_relational_reader(file_system)
    rr.instance_options["raise_error_on_missing_relation"] = False
    tfc = create_translation_file_cache(file_system)
    otfc = create_ot_file_cache(file_system)

    selected_modules = [m for m in modules if m.__name__ in selected_module_names]
    for parser_module in selected_modules:
        print("Running module '%s'" % parser_module.__name__)
        parser_module.write(
            file_system=file_system,
            data_path=__DATA_PATH__,
            relational_reader=rr,
            translation_file_cache=tfc,
            ot_file_cache=otfc,
        )

    # This forces the globals to be up to date with what we just parsed, in case someone uses `run_parser` within a script
    reload(RePoE)


if __name__ == "__main__":
    main()
