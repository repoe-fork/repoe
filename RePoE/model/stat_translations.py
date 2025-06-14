# generated by datamodel-codegen:
#   filename:  stat_translations.json
#   version:   0.28.5

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, RootModel


class Condition(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    min: Optional[int] = None
    max: Optional[int] = None
    negated: Optional[bool] = None


class OptionElement(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    id: int
    text: str


class Format(Enum):
    ignore = "ignore"
    field_ = "#"
    field__ = "+#"


class IndexHandler(RootModel[str]):
    root: str


class Type(RootModel[str]):
    root: str


class Stat(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    condition: List[Condition]
    format: List[Format]
    index_handlers: List[List[IndexHandler]]
    string: str
    reminder_text: Optional[str] = None
    is_markup: Optional[bool] = None


class TradeStatOption(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    options: List[OptionElement]


class TradeStat(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    id: str
    text: str
    type: Type
    option: Optional[TradeStatOption] = None


class StatTranslationsSchemaElement(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    English: Optional[List[Stat]] = None
    ids: List[str]
    trade_stats: Optional[List[TradeStat]] = None
    hidden: Optional[bool] = None
    French: Optional[List[Stat]] = None
    German: Optional[List[Stat]] = None
    Japanese: Optional[List[Stat]] = None
    Korean: Optional[List[Stat]] = None
    Portuguese: Optional[List[Stat]] = None
    Russian: Optional[List[Stat]] = None
    Spanish: Optional[List[Stat]] = None
    Thai: Optional[List[Stat]] = None
    Traditional_Chinese: Optional[List[Stat]] = Field(None, alias="Traditional Chinese")


class Model(RootModel[List[StatTranslationsSchemaElement]]):
    root: List[StatTranslationsSchemaElement]
