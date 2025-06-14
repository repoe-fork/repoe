# generated by datamodel-codegen:
#   filename:  crafting_bench_options.json
#   version:   0.28.5

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, RootModel


class Actions(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    change_socket_count: Optional[int] = None
    link_sockets: Optional[int] = None
    color_sockets: Optional[str] = None
    add_explicit_mod: Optional[str] = None
    remove_crafted_mods: Optional[bool] = None
    add_enchant_mod: Optional[str] = None
    remove_enchantments: Optional[bool] = None
    reroll_rarity: Optional[bool] = None


class ItemClass(RootModel[str]):
    root: str


class Master(RootModel[str]):
    root: str


class CraftingBenchOptionsSchemaElement(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    actions: Actions
    bench_tier: int
    cost: Dict[str, int]
    item_classes: List[ItemClass]
    master: Master


class Model(RootModel[List[CraftingBenchOptionsSchemaElement]]):
    root: List[CraftingBenchOptionsSchemaElement]
