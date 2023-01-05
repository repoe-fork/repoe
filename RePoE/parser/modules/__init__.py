import glob
import importlib
import inspect
from os.path import basename, dirname, isfile, join
from typing import List, cast

from RePoE.parser import Parser_Module


def _get_child_classes(module: Parser_Module, parent_class: type) -> List[type]:
    child_classes = []
    for name, obj in inspect.getmembers(module):
        if inspect.isclass(obj) and obj.__bases__[0] == parent_class:
            child_classes.append(obj)
    return child_classes


def get_all_modules() -> List[Parser_Module]:
    file_names = glob.glob(join(dirname(__file__), "*.py"))
    module_strings = [basename(f)[:-3] for f in file_names if isfile(f) and not f.endswith("__init__.py")]
    return cast(
        List[Parser_Module],
        [importlib.import_module(f"RePoE.parser.modules.{module_string}") for module_string in module_strings],
    )


def get_parser_modules() -> List[type]:
    parser_modules = []

    for module in get_all_modules():
        classes = _get_child_classes(module, Parser_Module)
        for parser_module in classes:
            parser_modules.append(parser_module)

        if len(classes) == 0:
            print(f"Warning: module {module} has no Parser_Module")

    return parser_modules
