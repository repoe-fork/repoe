import argparse
import os
from importlib import reload

import RePoE
from RePoE import __DATA_PATH__, __POE2_DATA_PATH__
from RePoE.parser.modules import get_parser_modules
from RePoE.parser.poe2 import get_poe2_modules
from RePoE.parser.util import create_relational_reader, get_cdn_url, load_file_system
import requests

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
    modules1 = get_parser_modules()
    modules2 = get_poe2_modules()

    module_names = list(set(module.__name__ for module in modules1 + modules2))
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
    parser.add_argument("-2", "--poe2", action=argparse.BooleanOptionalAction)
    parser.add_argument("-f", "--file", help="path to your Content.ggpk file")
    parser.add_argument("-l", "--language", default="English", choices=list(LANGS.keys()) + ["all"])
    args = parser.parse_args()

    print("Loading GGPK ...", end="", flush=True)
    file_system = load_file_system(args.file or get_cdn_url(2 if args.poe2 else 1))
    print(" Done!")

    modules = modules2 if args.poe2 else modules1
    if not args.module_names or "all" in args.module_names:
        modules.sort(key=lambda m: m.__name__)
    else:
        modules = [next(m for m in modules if m.__name__ == name) for name in args.module_names]

    for language in LANGS.keys() if args.language == "all" else [args.language]:

        data_path = __POE2_DATA_PATH__ if args.poe2 else __DATA_PATH__
        data_path = data_path if language == "English" else os.path.join(data_path, language, "")
        rr = create_relational_reader(file_system, language, args.poe2)
        caches = {}

        for parser_module in modules:
            print(f"Running module '{parser_module.__name__}' ({language})")
            parser_module(
                file_system=file_system,
                data_path=data_path,
                relational_reader=rr,
                language=language,
                caches=caches,
                sequel=2 if args.poe2 else 1,
            ).write()

    # This forces the globals to be up to date with what we just parsed,
    # in case someone uses `run_parser` within a script
    reload(RePoE)


if __name__ == "__main__":
    main()
