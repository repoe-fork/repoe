import argparse
import os
from importlib import reload

import RePoE
from RePoE import __DATA_PATH__
from RePoE.parser.modules import get_parser_modules
from RePoE.parser.util import DEFAULT_GGPK_PATH, create_relational_reader, load_file_system

# Codes taken from the 'preferred language' setting at https://www.pathofexile.com/my-account/preferences
LANGS = {
    "English": "en_US.utf8",
    "French": "fr_FR.utf8",
    "German": "de_DE.utf8",
    "Japanese": "ja_JP.utf8",
    "Korean": "ko_KR.utf8",
    "Portuguese": "pt_BR.utf8",
    "Russian": "ru_RU.utf8",
    "Spanish": "es_ES.utf8",
    "Thai": "th_TH.utf8",
    # Chinese not present in the settings, should this be zh_Hant.utf8?
    "Traditional Chinese": "zh_TW.utf8",
}


def main():
    modules = get_parser_modules()

    module_names = [module.__name__ for module in modules]
    module_names.sort()
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
    parser.add_argument("-l", "--language", default="English", choices=list(LANGS.keys()) + ["all"])
    args = parser.parse_args()

    print("Loading GGPK ...", end="", flush=True)
    file_system = load_file_system(args.file)
    print(" Done!")

    selected_module_names = args.module_names
    if "all" in selected_module_names:
        selected_module_names = [m for m in module_names if m != "all"]

    for language in LANGS.keys() if args.language == "all" else [args.language]:

        data_path = __DATA_PATH__ if language == "English" else os.path.join(__DATA_PATH__, language, "")

        rr = create_relational_reader(file_system, language)

        for name in selected_module_names:
            parser_module = next(m for m in modules if m.__name__ == name)
            print(f"Running module '{parser_module.__name__}' ({language})")
            parser_module(file_system=file_system, data_path=data_path, relational_reader=rr, language=language).write()

    # This forces the globals to be up to date with what we just parsed,
    # in case someone uses `run_parser` within a script
    reload(RePoE)


if __name__ == "__main__":
    main()
