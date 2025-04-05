import re
from typing import Any, Dict, List, Optional, Tuple, Union

from PyPoE.poe.file.dat import DatRecord, RelationalReader
from PyPoE.poe.file.file_system import FileSystem
from PyPoE.poe.file.translations import TranslationFileCache, TranslationString, TranslationFile

from RePoE.parser import Parser_Module
from RePoE.parser.constants import COOLDOWN_BYPASS_TYPES
from RePoE.parser.util import call_with_default_args, write_any_json


def _extract_static(obj):
    gepls_dict: Dict = obj["per_level"]
    if len(gepls_dict) >= 1:
        representative = next(reversed(gepls_dict.values()), None)
        static, _ = _handle_dict(representative, gepls_dict.values())

        stat_order = {}
        for level in gepls_dict.values():
            if "stat_order" in level:
                stat_order.update(level["stat_order"])
                del level["stat_order"]

        static = static or {}
        static["tooltip_order"] = [
            stat for stat, _ in
            sorted(
                list((stat_order | static.get("stat_order", {})).items()),
                key=lambda kv: kv[1]
            )
        ]
        if len(static["tooltip_order"]) == 0:
            del static["tooltip_order"]
        if "stat_order" in static:
            del static["stat_order"]

        if static is not None:
            obj["static"] = static


def _handle_dict(representative: Dict[str, Any], per_level: List[Dict[str, Any]]):
    static = None
    cleared = True
    cleared_keys = []
    for k, v in representative.items():
        per_level_values = []
        skip = False
        for pl in per_level:
            if k not in pl:
                skip = True
                break
            per_level_values.append(pl[k])
        if skip:
            cleared = False
            continue

        if isinstance(v, dict):
            static_value, cleared_value = _handle_dict(v, per_level_values)
        elif isinstance(v, list):
            static_value, cleared_value = _handle_list(v, per_level_values)
        else:
            static_value, cleared_value = _handle_primitives(v, per_level_values)

        if static_value is not None:
            if static is None:
                static = {}
            static[k] = static_value

        if cleared_value:
            cleared_keys.append(k)
        else:
            cleared = False

    for k in cleared_keys:
        for pl in per_level:
            del pl[k]
    return static, cleared


def _handle_list(
        representative: List[Dict[str, Any]], per_level: List[List[Optional[Dict[str, Any]]]]
) -> Tuple[Optional[List[Optional[Dict[str, Any]]]], bool]:
    # edge cases (all None, any None, mismatching lengths, all empty)
    all_none = True
    any_none = False
    for pl in per_level:
        all_none &= pl is None
        any_none |= pl is None
        if pl is not None and len(pl) != len(representative):
            return None, False
    if all_none:
        return None, True
    if any_none:
        return None, False
    if not representative:
        # all empty, else above would be true
        return [], True

    static: Optional[List[Optional[Dict[str, Any]]]] = None
    cleared = True
    cleared_is = []
    for i, v in enumerate(representative):
        per_level_values = [pl[i] for pl in per_level]
        if isinstance(v, dict):
            static_value, cleared_value = _handle_dict(v, per_level_values)
        elif isinstance(v, list):
            static_value, cleared_value = _handle_list(v, per_level_values)
        else:
            static_value, cleared_value = _handle_primitives(v, per_level_values)

        if static_value is not None:
            if static is None:
                static = [None] * len(representative)
            static[i] = static_value

        if cleared_value:
            cleared_is.append(i)
        else:
            cleared = False

    for i in cleared_is:
        for pl in per_level:
            pl[i] = None
    return static, cleared


def _handle_primitives(
        representative: Union[int, str], per_level: Union[List[int], List[str]]
) -> Tuple[Union[None, int, str], bool]:
    for pl in per_level:
        if pl != representative:
            return None, False
    return representative, True


class GemConverter:
    regex_number = re.compile(r"-?\d+(\.\d+)?")

    def __init__(
            self,
            file_system: FileSystem,
            relational_reader: RelationalReader,
            translation_file_cache: TranslationFileCache,
            language: str,
    ) -> None:
        self.relational_reader = relational_reader
        self.translation_file_cache = translation_file_cache
        self.language = language

        self.gepls: Dict[str, List[DatRecord]] = {}
        for gepl in self.relational_reader["GrantedEffectsPerLevel.dat64"]:
            ge_id = gepl["GrantedEffect"]["Id"]
            self.gepls.setdefault(ge_id, []).append(gepl)

        self.gesspls: Dict[str, List[Any]] = {}
        for gesspl in self.relational_reader["GrantedEffectStatSetsPerLevel.dat64"]:
            gess_id = gesspl["StatSet"]["Id"]
            if gess_id not in self.gesspls:
                self.gesspls[gess_id] = []
            self.gesspls[gess_id].append(gesspl)

        self.granted_effect_quality_stats: Dict[str, Any] = {}
        for geq in self.relational_reader["GrantedEffectQualityStats.dat64"]:
            ge_id = geq["GrantedEffectsKey"]["Id"]
            if ge_id not in self.granted_effect_quality_stats:
                self.granted_effect_quality_stats[ge_id] = []
            self.granted_effect_quality_stats[ge_id].append(geq)

        self.tags = {}
        for tag in self.relational_reader["GemTags.dat64"]:
            name = tag["Name"]
            self.tags[tag["Id"]] = name if name != "" else None

        self.max_levels: Dict[str, int] = {}
        for row in self.relational_reader["ItemExperiencePerLevel.dat64"]:
            base_item = row["ItemExperienceType"]["Id"]
            level = row["ItemCurrentLevel"]
            if base_item not in self.max_levels:
                self.max_levels[base_item] = level
            elif self.max_levels[base_item] < level:
                self.max_levels[base_item] = level

        self._skill_totem_life_multipliers = {}
        for row in self.relational_reader["SkillTotemVariations.dat64"]:
            self._skill_totem_life_multipliers[row["SkillTotemsKey"]] = (
                    row["MonsterVarietiesKey"]["LifeMultiplier"] / 100
            )

    def _convert_active_skill(self, active_skill: DatRecord) -> Dict[str, Any]:
        stat_conversions = {}
        for in_stat, out_stat in zip(active_skill["Input_Stats"], active_skill["Output_Stats"]):
            stat_conversions[in_stat["Id"]] = out_stat["Id"]
        skill_totem_id = active_skill["SkillTotemId"]
        is_skill_totem = skill_totem_id is not None and skill_totem_id in self._skill_totem_life_multipliers
        r = {
            "id": active_skill["Id"],
            "display_name": active_skill["DisplayedName"],
            "description": active_skill["Description"],
            "types": self._select_active_skill_types(active_skill["ActiveSkillTypes"]),
            "weapon_restrictions": [],  # TODO: ActiveSkillWeaponRequirement.dat
            "is_skill_totem": is_skill_totem,
            "is_manually_casted": active_skill["IsManuallyCasted"],
            "stat_conversions": stat_conversions,
        }
        if is_skill_totem:
            r["skill_totem_life_multiplier"] = self._skill_totem_life_multipliers[skill_totem_id]
        if active_skill["MinionActiveSkillTypes"]:
            r["minion_types"] = self._select_active_skill_types(
                active_skill["MinionActiveSkillTypes"])
        return r

    @classmethod
    def _convert_support_gem_specific(cls, granted_effect: DatRecord) -> Dict[str, Any]:
        return {
            "letter": granted_effect["SupportGemLetter"],
            "supports_gems_only": granted_effect["SupportsGemsOnly"],
            "allowed_types": cls._select_active_skill_types(
                granted_effect["AllowedActiveSkillTypes"]),
            "excluded_types": cls._select_active_skill_types(
                granted_effect["ExcludedActiveSkillTypes"]),
            "added_types": cls._select_active_skill_types(granted_effect["AddedActiveSkillTypes"]),
            "added_minion_types": cls._select_active_skill_types(
                granted_effect["AddedMinionActiveSkillTypes"]),
        }

    @staticmethod
    def _select_active_skill_types(type_rows: List[DatRecord]) -> List[str]:
        return [row["Id"] for row in type_rows] if type_rows else None

    def get_translation(self, string: TranslationString):
        s = []
        for i, tag in enumerate(string.tags):
            q = [string.translation.ids[tag]]
            for k, v in string.quantifier.index_handlers.items():
                if tag + 1 in v:
                    q.append(k)
            s.append(string.strings[i])
            s.append(f'{{{"/".join(q)}}}')
        s.append(string.strings[-1])
        return "".join(s)

    def _convert_gepl(
            self,
            granted_effect: DatRecord,
            gepl: DatRecord,
            is_support: bool,
    ) -> Dict[str, Any]:
        r = {}
        if gepl["Cooldown"] > 0:
            r["cooldown"] = gepl["Cooldown"]
            cooldown_bypass_type = COOLDOWN_BYPASS_TYPES(gepl["CooldownBypassType"])
            if cooldown_bypass_type is not COOLDOWN_BYPASS_TYPES.NONE:
                r["cooldown_bypass_type"] = cooldown_bypass_type.name.lower()
        if gepl["StoredUses"] > 0:
            r["stored_uses"] = gepl["StoredUses"]

        if is_support:
            r["cost_multiplier"] = gepl["CostMultiplier"]
        else:
            r["costs"] = {}
            for cost_type, cost_amount in zip(granted_effect["CostTypes"], gepl["CostAmounts"]):
                r["costs"][cost_type["Id"]] = cost_amount
            if gepl["AttackSpeedMultiplier"] != 0:
                r["attack_speed_multiplier"] = gepl["AttackSpeedMultiplier"]
            if gepl["VaalSouls"] > 0:
                r["vaal"] = {"souls": gepl["VaalSouls"], "stored_uses": gepl["VaalStoredUses"]}

        r["reservations"] = self._convert_reservations(gepl)
        return r

    def _convert_gess(
            self,
            granted_effect: DatRecord,
            gess: DatRecord,
            gesspl: DatRecord,
            translation_file: TranslationFile,
            primary_gess: DatRecord,
            primary_gesspl: DatRecord
    ) -> Dict[str, Any]:
        r = {}

        if gesspl["BaseMultiplier"] != 0:
            mult = 100 + gesspl["BaseMultiplier"] / 100
            r["damage_multiplier"] = int(mult) if mult == int(mult) else mult
        if gesspl["SpellCritChance"] or gesspl["AttackCritChance"]:
            r["crit_chance"] = gesspl["SpellCritChance"] or gesspl["AttackCritChance"]

        stats = []
        for k, v in zip(gesspl["FloatStats"], gesspl["BaseResolvedValues"]):
            stats.append({"id": k["Id"], "value": v, "type": "float"})
        for k, v in zip(gess["ConstantStats"], gess["ConstantStatsValues"]):
            stats.append({"id": k["Id"], "value": v, "type": "constant"})
        for k, v in zip(gesspl["AdditionalStats"], gesspl["AdditionalStatsValues"]):
            stats.append({"id": k["Id"], "value": v, "type": "additional"})
        for k in gess["ImplicitStats"]:
            stats.append({"id": k["Id"], "value": 1, "type": "implicit"})
        for k in gesspl["AdditionalFlags"]:
            stats.append({"id": k["Id"], "value": 1, "type": "flag"})

        # copy stats from primary stat set
        if gess != primary_gess:
            ignored_stats = gess["IgnoredStats"]
            for k, v in zip(primary_gesspl["FloatStats"], primary_gesspl["BaseResolvedValues"]):
                if k not in ignored_stats:
                    stats.append({"id": k["Id"], "value": v, "type": "float"})
            for k, v in zip(primary_gess["ConstantStats"], primary_gess["ConstantStatsValues"]):
                if k not in ignored_stats:
                    stats.append({"id": k["Id"], "value": v, "type": "constant"})
            for k, v in zip(primary_gesspl["AdditionalStats"], primary_gesspl["AdditionalStatsValues"]):
                if k not in ignored_stats:
                    stats.append({"id": k["Id"], "value": v, "type": "constant"})
            for k in primary_gess["ImplicitStats"]:
                if k not in ignored_stats:
                    stats.append({"id": k["Id"], "value": 1, "type": "implicit"})

        # consolidate duplicate stats with summed values
        stat_map = {}
        for stat in stats:
            k = stat["id"]
            if k not in stat_map:
                stat_map[k] = stat
            elif stat["type"] != "implicit":
                stat_map[k]["value"] += stat["value"]
        stats = list(stat_map.values())

        r["stats"] = stats

        try:
            stat_text = {}
            value_map = {}
            for v in stats:
                if v["value"]:
                    value_map[v["id"]] = v["value"]

            trans = translation_file.get_translation(
                list(value_map.keys()), value_map, full_result=True, lang=self.language
            )

            stat_order = {}
            for i, stats in enumerate(trans.found_ids):
                stats = [stat for stat in stats if value_map.get(stat, None)]
                key = "\n".join(stats)
                stat_text[key] = trans.found_lines[i]
                stat_order[key] = trans.tf_indices[i]

            r["stat_order"] = stat_order
            r["stat_text"] = stat_text
        except Exception as e:
            print("Error processing stat text for", stats, e)
            pass

        q_stats = []

        if granted_effect["Id"] in self.granted_effect_quality_stats:
            for geq in self.granted_effect_quality_stats[granted_effect["Id"]]:
                stats = {
                    r["Id"]: geq["StatsValuesPermille"][i]
                    for i, r in enumerate(geq["StatsKeys"])
                    if geq["StatsValuesPermille"][i] is not None
                }
                if not stats:
                    continue
                q_stat = {"stats": stats}
                tag_count = -1
                for value in sorted(
                        set([min(1000, abs(v)) for v in stats.values() if v] + [25])):
                    trans = translation_file.get_translation(
                        list(stats.keys()), {k: v / value for k, v in stats.items()},
                        full_result=True, lang=self.language
                    )
                    tags = sum(len(i.tags) for i in trans.string_instances)
                    if sum(len(i.tags) for i in trans.string_instances) > tag_count:
                        tag_count = tags
                        q_stat["stat"] = "\n".join(
                            self.get_translation(string) for string in trans.string_instances)
                q_stats.append(q_stat)
            r["quality_stats"] = q_stats

        return r

    @staticmethod
    def _convert_reservations(gepl: DatRecord):
        if gepl["Reservation"] > 0:
            return {"spirit": gepl["Reservation"]}
        return None

    def convert_skill(
            self,
            granted_effect: DatRecord,
    ) -> Dict[str, Any]:
        is_support = granted_effect["IsSupport"]
        obj = {"is_support": is_support}

        if is_support:
            obj["support_gem"] = self._convert_support_gem_specific(granted_effect)

        if granted_effect["ActiveSkill"]:
            obj["cast_time"] = granted_effect["CastTime"]
            obj["active_skill"] = self._convert_active_skill(granted_effect["ActiveSkill"])

        # GrantedEffectsPerLevel
        obj["stats"] = {}
        obj["per_level"] = {}
        gepls = self.gepls[granted_effect["Id"]]
        gepls.sort(key=lambda g: g["Level"])
        for gepl in gepls:
            gepl_converted = self._convert_gepl(
                granted_effect,
                gepl,
                is_support,
            )
            obj["per_level"][str(gepl["Level"])] = gepl_converted
        gesses = [granted_effect["StatSet"]] + (granted_effect["AdditionalStatSets"] or [])
        if gesses:
            obj["stat_sets"] = []
        for i, gess in enumerate(gesses):
            primary_gess = gesses[0]
            skill_id = obj.get("active_skill").get("id") if "active_skill" in obj else None
            translation_file = None
            game_file_name = None
            for game_file_name in self._get_possible_translation_files(skill_id, i):
                try:
                    translation_file = self.translation_file_cache[game_file_name]
                    break
                except (KeyError, FileNotFoundError):
                    pass
                except:
                    print("Unexpected error in translation file", game_file_name)
                    raise
            gepls_dict = {}
            for gesspl, primary_gesspl in zip(self.gesspls[gess["Id"]], self.gesspls[primary_gess["Id"]]):
                gepls_dict[gesspl["GemLevel"]] = self._convert_gess(
                    granted_effect,
                    gess,
                    gesspl,
                    translation_file,
                    primary_gess,
                    primary_gesspl
                )
            obj["stat_sets"].append({
                "id": gess["Id"],
                "per_level": gepls_dict,
                "translation_file": game_file_name,
                "label": gess["Label"],
            })

        return obj

    @staticmethod
    def _get_possible_translation_files(
            active_skill: Optional[str],
            stat_set: int | None,
    ) -> List[str]:
        if active_skill is None:
            return ["gem_stat_descriptions.txt"]
        else:
            return [
                f"specific_skill_stat_descriptions/{active_skill}/statset_{stat_set}.csd",
                f"specific_skill_stat_descriptions/{active_skill}.csd",
                "skill_stat_descriptions.txt"
            ]


class skills(Parser_Module):
    def write(self) -> None:
        skills: dict[str, dict] = {}
        relational_reader = self.relational_reader
        converter = GemConverter(
            self.file_system, relational_reader, self.get_cache(TranslationFileCache), self.language
        )

        # Default Attack/PlayerMelee is neither gem nor mod effect
        for granted_effect in relational_reader["GrantedEffects.dat64"]:
            ge_id = granted_effect["Id"]
            skill = converter.convert_skill(granted_effect)
            _extract_static(skill)
            for stat_set in skill.get("stat_sets", []):
                _extract_static(stat_set)
            skills[ge_id] = skill

        write_any_json(skills, self.data_path, "skills")


if __name__ == "__main__":
    call_with_default_args(skills)
