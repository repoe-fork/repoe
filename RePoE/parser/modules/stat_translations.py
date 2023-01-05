from PyPoE.poe.file.translations import get_custom_translation_file
from RePoE.parser.util import write_json, call_with_default_args, get_stat_translation_file_name
from RePoE.parser import Parser_Module
from PyPoE.poe.file.dat import RelationalReader
from PyPoE.poe.file.file_system import FileSystem
from PyPoE.poe.file.ot import OTFileCache
from PyPoE.poe.file.translations import TranslationFileCache
from typing import List
from PyPoE.poe.file.translations import TranslationRange
from typing import Dict
from typing import Union
from PyPoE.poe.file.translations import Translation
from typing import Any
from typing import Set
from typing import Iterator
from typing import Tuple


def _convert_tags(n_ids: int, tags: List[int], tags_types: List[str]) -> List[str]:
    f = ["ignore" for _ in range(n_ids)]
    for tag, tag_type in zip(tags, tags_types):
        if tag_type == "+d":
            f[tag] = "+#"
        elif tag_type == "d":
            f[tag] = "#"
        elif tag_type == "":
            f[tag] = "#"
        else:
            print("Unknown tag type:", tag_type)
    return f


def _convert_range(translation_range: List[TranslationRange]) -> Union[List[Dict[str, int]], List[Dict]]:
    rs = []
    for r in translation_range:
        r_dict = {}
        if r.min is not None:
            r_dict["min"] = r.min
        if r.max is not None:
            r_dict["max"] = r.max
        if r.negated:
            r_dict["negated"] = True
        rs.append(r_dict)
    return rs


def _convert_handlers(n_ids: int, index_handlers: Dict) -> Union[List[List[str]], List[List]]:
    hs: List[List[str]] = [[] for _ in range(n_ids)]
    for handler_name, ids in index_handlers.items():
        for i in ids:
            # Indices in the handler dict are 1-based
            hs[i - 1].append(handler_name)
    return hs


def _convert(tr: Translation, tag_set: Set[str]) -> Dict[str, Any]:
    ids = tr.ids
    n_ids = len(ids)
    english = []
    for s in tr.get_language("English").strings:
        tags = _convert_tags(n_ids, s.tags, s.tags_types)
        tag_set.update(tags)
        english.append(
            {
                "condition": _convert_range(s.range),
                "string": s.as_format_string,
                "format": tags,
                "index_handlers": _convert_handlers(n_ids, s.quantifier.index_handlers),
            }
        )
    return {"ids": ids, "English": english}


def _get_stat_translations(
    tag_set: Set[str], translations: List[Translation], custom_translations: List[Translation]
) -> List[Dict[str, Any]]:
    previous = set()
    root = []
    for tr in translations:
        id_str = " ".join(tr.ids)
        if id_str in previous:
            print("Duplicate id", tr.ids)
            continue
        previous.add(id_str)
        root.append(_convert(tr, tag_set))
    for tr in custom_translations:
        id_str = " ".join(tr.ids)
        if id_str in previous:
            continue
        previous.add(id_str)
        result = _convert(tr, tag_set)
        result["hidden"] = True
        root.append(result)
    return root


def _build_stat_translation_file_map(file_system: FileSystem) -> Iterator[Tuple[str, str]]:
    node = file_system.build_directory()
    for game_file in node["Metadata"]["StatDescriptions"].children.keys():
        out_file = get_stat_translation_file_name(game_file)
        if out_file:
            yield game_file, out_file


class stat_translations(Parser_Module):
    @staticmethod
    def write(
        file_system: FileSystem,
        data_path: str,
        relational_reader: RelationalReader,
        translation_file_cache: TranslationFileCache,
        ot_file_cache: OTFileCache,
    ) -> None:
        tag_set: Set[str] = set()
        for in_file, out_file in _build_stat_translation_file_map(file_system):
            translations = translation_file_cache[in_file].translations
            result = _get_stat_translations(tag_set, translations, get_custom_translation_file().translations)
            write_json(result, data_path, out_file)
        print("Possible format tags: {}".format(tag_set))


if __name__ == "__main__":
    call_with_default_args(stat_translations.write)
