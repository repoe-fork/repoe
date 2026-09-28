"""Mercenaries of Trarthus: builds, classes, skills, supports, flavour text and the
mercenary gear panel, from the 14 Mercenary tables.

Writes six files, each keyed by the row's game id:

- mercenary_builds.json: MercenaryBuilds with their extra stats, weapon item classes
  and cosmetic overrides. Each Infamous build sits inside the regular build whose id it
  extends with "Noble", as `infamous`: its id and name plus every other field whose
  value differs. An Infamous build with no regular build of that id stays a build.
- mercenary_classes.json: MercenaryClasses with their attribute.
- mercenary_skills.json: MercenarySkills keyed by granted effect id, with the granted
  effect converted the way gems.json converts gems.
- mercenary_supports.json: MercenarySupports with stat_text rendered through
  mercenary_support_stat_descriptions.txt, which stat_translation_file names.
- mercenary_flavour_text.json: MercenaryFlavourText with its tag weights.
- mercenary_inventories.json: the slots of the mercenary gear panel.

Every row is exported, placeholder rows included. Unknown, Data and HASH16 columns are
not exported.
"""

from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

from PyPoE.poe.file.translations import TranslationFileCache

from RePoE.parser import Parser_Module
from RePoE.parser.modules.gems import GemConverter
from RePoE.parser.util import (
    call_with_default_args,
    export_image,
    get_id_or_none,
    get_stat_translation_file_name,
    write_json,
)

# An Infamous build's id is its regular build's id with this suffix
# (AurasMinionsTemplarSmite, AurasMinionsTemplarSmiteNoble).
INFAMOUS_ID_SUFFIX = "Noble"

SUPPORT_STAT_DESCRIPTIONS = "mercenary_support_stat_descriptions.txt"
SUPPORT_STAT_TRANSLATION_FILE = get_stat_translation_file_name(SUPPORT_STAT_DESCRIPTIONS)

# The GemConverter.convert(None, granted_effect) fields each skill carries. Top-level and
# active_skill fields are filtered to these; per_level and static are copied whole.
CONVERTED_SKILL_FIELDS = ("cast_time", "active_skill", "stat_translation_file", "per_level", "static", "tooltip_order")
ACTIVE_SKILL_FIELDS = (
    "id",
    "display_name",
    "description",
    "types",
    "weapon_restrictions",
    "is_skill_totem",
    "is_manually_casted",
    "stat_conversions",
    "skill_totem_life_multiplier",
    "minion_types",
)


def ids(rows: Iterable[Any]) -> List[str]:
    return [row["Id"] for row in rows]


def skill_id(row: Any) -> str:
    granted_effect = row["GrantedEffect"]
    if granted_effect is None:
        raise ValueError(f"MercenarySkills row {row['Name']!r} has no GrantedEffect")
    return granted_effect["Id"]


def skill_pool(count: int, rows: Iterable[Any]) -> Dict[str, Any]:
    return {"count": count, "pool": [skill_id(row) for row in rows]}


def keyed(pairs: Iterable[Tuple[str, Dict[str, Any]]], table: str) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for key, entry in pairs:
        if key in out:
            raise ValueError(f"{table}: duplicate id {key}")
        out[key] = entry
    return out


def extra_stat_entry(row: Any) -> Dict[str, Any]:
    category = row["Category"]
    return {
        "id": row["Id"],
        "stat_id": row["Stat"]["Id"],
        "level24": row["Level24"],
        "level68": row["Level68"],
        "level84": row["Level84"],
        "category": None if category is None else {"id": category["Id"], "name": category["Name"]},
    }


def visual_override_entry(row: Any) -> Dict[str, Any]:
    mtx = row["MtxGameSpecific"]
    return {
        "slot_id": row["SlotId"],
        "mtx_type": None if mtx is None else get_id_or_none(mtx["Type"]),
        "dds_file": None if mtx is None else mtx["DDSFile"],
    }


def build_entry(row: Any, visual_overrides: List[Dict[str, Any]]) -> Dict[str, Any]:
    idle_skill = row["IdleSkill"]
    return {
        "name": row["Name"],
        "class_id": row["Class"]["Id"],
        "is_infamous": bool(row["IsInfamous"]),
        "primary_skills": [skill_id(skill) for skill in row["Skills1"]],
        "secondary_skills": skill_pool(row["Skills2Count"], row["Skills2"]),
        "utility_skills": skill_pool(row["Skills3Count"], row["Skills3"]),
        "idle_skill": None if idle_skill is None else skill_id(idle_skill),
        "tags": ids(row["Tags"]),
        "weapon_item_classes": [wieldable["ItemClass"]["Id"] for wieldable in row["WieldableTypes"]],
        "extra_stats": [extra_stat_entry(extra) for extra in row["ExtraStats"]],
        "achievements": ids(row["Achievements"]),
        "visual_overrides": visual_overrides,
        "ai_file": row["AIFile"],
    }


def infamous_entry(infamous_id: str, infamous: Dict[str, Any], regular: Dict[str, Any]) -> Dict[str, Any]:
    entry = {"id": infamous_id, "name": infamous["name"]}
    for field, value in infamous.items():
        if field in ("name", "is_infamous") or value == regular[field]:
            continue
        if value is None:
            raise ValueError(f"Infamous build {infamous_id} has no {field} where its regular build has one")
        entry[field] = value
    return entry


def pair_infamous(builds: Dict[str, Dict[str, Any]]) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
    """Each Infamous build inside its regular build, paired by id alone. Returns the
    builds and the Infamous ids left as builds of their own."""
    out = {build_id: dict(entry, infamous=None) for build_id, entry in builds.items() if not entry["is_infamous"]}
    unpaired = []
    for build_id, entry in builds.items():
        if not entry["is_infamous"]:
            continue
        regular_id = build_id[: -len(INFAMOUS_ID_SUFFIX)] if build_id.endswith(INFAMOUS_ID_SUFFIX) else None
        pairable = regular_id in builds and not builds[regular_id]["is_infamous"]
        if not pairable:
            out[build_id] = dict(entry, infamous=None)
            unpaired.append(build_id)
            continue
        out[regular_id]["infamous"] = infamous_entry(build_id, entry, builds[regular_id])
    return out, unpaired


def class_entry(row: Any) -> Dict[str, Any]:
    attribute = row["Attribute"]
    return {
        "house_name": row["HouseName"],
        "attribute": {"id": attribute["Id"], "name": attribute["Name"], "tags": ids(attribute["Tags"])},
        "monster_variety": get_id_or_none(row["MonsterVariety"]),
        "monster_variety_allied": get_id_or_none(row["MonsterVarietyAllied"]),
        "terrain_feature": get_id_or_none(row["TerrainFeature"]),
        "house_spawn_chance_stats": ids(row["HouseSpawnChanceStats"]),
        "attribute_spawn_chance_stats": ids(row["AttributeSpawnChanceStats"]),
        "class_icon": row["ClassIcon"],
        "house_icon": row["HouseIcon"],
        "house_buff_icon": row["HouseBuffIcon"],
    }


def copy_converted(converted: Dict[str, Any]) -> Dict[str, Any]:
    out = {field: converted[field] for field in CONVERTED_SKILL_FIELDS if field in converted}
    if out.get("active_skill") is not None:
        out["active_skill"] = {
            field: out["active_skill"][field] for field in ACTIVE_SKILL_FIELDS if field in out["active_skill"]
        }
    return out


def skill_entry(
    row: Any, convert: Callable[[Any], Dict[str, Any]], fail_fast: bool
) -> Tuple[Dict[str, Any], Optional[str]]:
    """The skill and, when its granted effect converts, the converted fields. A granted
    effect the converter cannot handle comes back as an error string so one skill does
    not stop the other files, unless fail_fast is set, in which case it raises."""
    skill_id(row)
    granted_effect = row["GrantedEffect"]
    active_skill = granted_effect["ActiveSkill"]
    entry = {
        "name": row["Name"],
        "description": row["Description"],
        "required_level": row["RequiredLevel"],
        "support_count": get_id_or_none(row["SupportCount"]),
        "possible_supports": ids(row["PossibleSupports"]),
        "family": get_id_or_none(row["SkillFamily"]),
        "encounter_granted_effect": get_id_or_none(row["EncounterGrantedEffect"]),
        "house_icon": row["HouseIcon"],
        "icon": None if active_skill is None else active_skill["Icon_DDSFile"],
    }
    try:
        converted = convert(granted_effect)
    except Exception as error:
        if fail_fast:
            raise
        return entry, f"{type(error).__name__}: {error}"
    entry.update(copy_converted(converted))
    return entry, None


def stat_text(stats: List[Dict[str, Any]], translate: Callable[[Dict[str, int]], Any]) -> Dict[str, str]:
    """Rendered lines keyed by the ids of the stats each line shows, joined by a newline:
    the shape gems.json gives stat_text."""
    values: Dict[str, int] = {}
    for stat in stats:
        if stat["value"]:
            values[stat["id"]] = values.get(stat["id"], 0) + stat["value"]
    if not values:
        return {}
    result = translate(values)
    text = {}
    for i, found in enumerate(result.found_ids):
        text["\n".join(stat for stat in found if values.get(stat))] = result.found_lines[i]
    return text


def support_entry(row: Any, translate: Callable[[Dict[str, int]], Any]) -> Dict[str, Any]:
    stat_ids = ids(row["Stats"])
    values = list(row["StatValues"])
    if len(stat_ids) != len(values):
        raise ValueError(f"MercenarySupports {row['Id']}: {len(stat_ids)} stats but {len(values)} values")
    stats = [{"id": stat, "value": value} for stat, value in zip(stat_ids, values)]
    return {
        "name": row["Name"],
        "tier": row["Tier"],
        "family": get_id_or_none(row["SupportFamily"]),
        "icon": row["GemIcon"],
        "stat_translation_file": SUPPORT_STAT_TRANSLATION_FILE,
        "stats": stats,
        "stat_text": stat_text(stats, translate),
    }


def flavour_text_entry(row: Any) -> Dict[str, Any]:
    tags = ids(row["Tags"])
    weights = list(row["TagWeight"])
    if len(tags) != len(weights):
        raise ValueError(f"MercenaryFlavourText {row['Id']}: {len(tags)} tags but {len(weights)} weights")
    return {"text": row["Description"], "tag_weights": [{"tag": t, "weight": w} for t, w in zip(tags, weights)]}


def inventory_entry(row: Any) -> Dict[str, Any]:
    return {"position_x": row["PositionX"], "position_y": row["PositionY"]}


class mercenaries(Parser_Module):
    def write(self) -> None:
        reader = self.relational_reader
        translations = self.get_cache(TranslationFileCache)
        support_stats = translations[SUPPORT_STAT_DESCRIPTIONS]
        converter = GemConverter(self.file_system, reader, translations, self.language)

        def translate(values: Dict[str, int]) -> Any:
            return support_stats.get_translation(values.keys(), values, full_result=True, lang=self.language)

        overrides: Dict[str, List[Dict[str, Any]]] = {}
        for row in reader["MercenaryBuildVisualOverrides.dat64"]:
            overrides.setdefault(row["Id"]["Id"], []).append(visual_override_entry(row))

        builds = keyed(
            ((row["Id"], build_entry(row, overrides.get(row["Id"], []))) for row in reader["MercenaryBuilds.dat64"]),
            "MercenaryBuilds",
        )
        builds, unpaired = pair_infamous(builds)
        paired = sorted(build_id for build_id, build in builds.items() if build["infamous"] is not None)
        print(f"mercenaries: {len(paired)} Infamous builds inside their regular build, {len(unpaired)} on their own")
        for build_id in unpaired:
            print(f"  on its own: {build_id}")

        skill_rows: List[Tuple[str, Dict[str, Any]]] = []
        failed: List[Tuple[str, str]] = []
        for row in reader["MercenarySkills.dat64"]:
            entry, error = skill_entry(
                row, lambda granted_effect: converter.convert(None, granted_effect), self.fail_fast
            )
            skill_rows.append((skill_id(row), entry))
            if error is not None:
                failed.append((skill_id(row), error))
        skills = keyed(skill_rows, "MercenarySkills")
        print(f"mercenaries: {len(failed)} of {len(skills)} granted effects did not convert")
        for key, error in failed:
            print(f"  {key}: {error}")

        supports = keyed(
            ((row["Id"], support_entry(row, translate)) for row in reader["MercenarySupports.dat64"]),
            "MercenarySupports",
        )
        classes = keyed(((row["Id"], class_entry(row)) for row in reader["MercenaryClasses.dat64"]), "MercenaryClasses")
        flavour_text = keyed(
            ((row["Id"], flavour_text_entry(row)) for row in reader["MercenaryFlavourText.dat64"]),
            "MercenaryFlavourText",
        )
        inventories = keyed(
            ((row["Id"]["Id"], inventory_entry(row)) for row in reader["MercenaryInventories.dat64"]),
            "MercenaryInventories",
        )

        if self.language == "English":
            self._export_icons(skills, supports)

        write_json(builds, self.data_path, "mercenary_builds")
        write_json(classes, self.data_path, "mercenary_classes")
        write_json(skills, self.data_path, "mercenary_skills")
        write_json(supports, self.data_path, "mercenary_supports")
        write_json(flavour_text, self.data_path, "mercenary_flavour_text")
        write_json(inventories, self.data_path, "mercenary_inventories")

    def _export_icons(self, skills: Dict[str, Dict[str, Any]], supports: Dict[str, Dict[str, Any]]) -> None:
        paths = {path for skill in skills.values() for path in (skill["icon"], skill["house_icon"]) if path}
        paths |= {support["icon"] for support in supports.values() if support["icon"]}
        missing = sorted(path for path in paths if not export_image(path, self.data_path, self.file_system))
        print(f"mercenaries: {len(missing)} of {len(paths)} icons not found")
        for path in missing:
            print(f"  {path}")


if __name__ == "__main__":
    call_with_default_args(mercenaries)
