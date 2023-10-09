from collections import defaultdict
import json
from typing import Any, Dict, Iterator, List, Set, Tuple, Union

from PyPoE.poe.file.file_system import FileSystem
from PyPoE.poe.file.translations import Translation, TranslationFileCache, TranslationRange, get_custom_translation_file
from urllib.request import urlopen, Request

from RePoE.parser import Parser_Module
from RePoE.parser.util import call_with_default_args, get_stat_translation_file_name, write_json


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


def _convert(tr: Translation, tag_set: Set[str], all_trade_stats: dict[str, list[dict]]) -> Dict[str, Any]:
    ids = tr.ids
    n_ids = len(ids)
    english = []
    trade_stats = defaultdict(list)
    for s in tr.get_language("English").strings:
        tags = _convert_tags(n_ids, s.tags, s.tags_types)
        tag_set.update(tags)
        format = s.as_format_string

        try:
            trade = format.format(*tags)
            if trade in all_trade_stats:
                for trade_stat in all_trade_stats[trade]:
                    trade_stats[trade_stat["id"]] = trade_stat
            else:
                for line in trade.splitlines():
                    if line in all_trade_stats:
                        for trade_stat in all_trade_stats[line]:
                            trade_stats[trade_stat["id"]] = trade_stat
        except Exception:
            # bad format string
            pass

        value = {
            "condition": _convert_range(s.range),
            "string": s.as_format_string,
            "format": tags,
            "index_handlers": _convert_handlers(n_ids, s.quantifier.index_handlers),
        }
        english.append(value)
    return {"ids": ids, "English": english, "trade_stats": list(trade_stats.values()) if trade_stats else None}


def _get_stat_translations(
    tag_set: Set[str], translations: List[Translation], custom_translations: List[Translation], trade_stats
) -> List[Dict[str, Any]]:
    previous = set()
    root = []
    for tr in translations:
        id_str = " ".join(tr.ids)
        if id_str in previous:
            print("Duplicate id", tr.ids)
            continue
        previous.add(id_str)
        root.append(_convert(tr, tag_set, trade_stats))
    for tr in custom_translations:
        id_str = " ".join(tr.ids)
        if id_str in previous:
            continue
        previous.add(id_str)
        result = _convert(tr, tag_set, trade_stats)
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
    def write(self) -> None:
        with urlopen(
            Request(
                "https://www.pathofexile.com/api/trade/data/stats",
                headers={"User-Agent": "OAuth RePoE/1.0.0 (contact: https://github.com/lvlvllvlvllvlvl/RePoE/)"},
            )
        ) as req:
            data = json.load(req)
            if "result" not in data:
                print(data)
            trade_stats = defaultdict(list)
            for trade_stat in [entry for v in data["result"] for entry in v["entries"]]:
                if "option" in trade_stat:
                    for option in trade_stat["option"]["options"]:
                        trade_stats[trade_stat["text"].replace("#", option["text"])].append(trade_stat)
                else:
                    trade_stats[trade_stat["text"]].append(trade_stat)

        tag_set: Set[str] = set()
        for in_file, out_file in _build_stat_translation_file_map(self.file_system):
            translations = self.get_cache(TranslationFileCache)[in_file].translations
            result = _get_stat_translations(
                tag_set, translations, get_custom_translation_file().translations, trade_stats
            )
            write_json(result, self.data_path, out_file)
        print("Possible format tags: {}".format(tag_set))


if __name__ == "__main__":
    call_with_default_args(stat_translations)
