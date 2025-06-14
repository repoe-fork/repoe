# generated by datamodel-codegen:
#   filename:  cluster_jewels.json
#   version:   0.28.5

from __future__ import annotations

from enum import Enum
from typing import Dict, List

from pydantic import BaseModel, ConfigDict, Field, RootModel


class PassiveSkill(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    id: str
    name: str
    stats: Dict[str, int]
    tag: str


class MetadataItemsJewelsJewelPassiveTreeExpansionLargeSize(Enum):
    Large = "Large"


class MetadataItemsJewelsJewelPassiveTreeExpansionMediumSize(Enum):
    Medium = "Medium"


class MetadataItemsJewelsJewelPassiveTreeExpansionSmallSize(Enum):
    Small = "Small"


class MetadataItemsJewelsJewelPassiveTreeExpansionLarge(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    max_skills: int
    min_skills: int
    name: str
    notable_indices: List[int]
    passive_skills: List[PassiveSkill]
    size: MetadataItemsJewelsJewelPassiveTreeExpansionLargeSize
    small_indices: List[int]
    socket_indices: List[int]
    total_indices: int


class MetadataItemsJewelsJewelPassiveTreeExpansionMedium(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    max_skills: int
    min_skills: int
    name: str
    notable_indices: List[int]
    passive_skills: List[PassiveSkill]
    size: MetadataItemsJewelsJewelPassiveTreeExpansionMediumSize
    small_indices: List[int]
    socket_indices: List[int]
    total_indices: int


class MetadataItemsJewelsJewelPassiveTreeExpansionSmall(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    max_skills: int
    min_skills: int
    name: str
    notable_indices: List[int]
    passive_skills: List[PassiveSkill]
    size: MetadataItemsJewelsJewelPassiveTreeExpansionSmallSize
    small_indices: List[int]
    socket_indices: List[int]
    total_indices: int


class ClusterJewelsSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    Metadata_Items_Jewels_JewelPassiveTreeExpansionLarge: MetadataItemsJewelsJewelPassiveTreeExpansionLarge = Field(
        ..., alias="Metadata/Items/Jewels/JewelPassiveTreeExpansionLarge"
    )
    Metadata_Items_Jewels_JewelPassiveTreeExpansionMedium: MetadataItemsJewelsJewelPassiveTreeExpansionMedium = Field(
        ..., alias="Metadata/Items/Jewels/JewelPassiveTreeExpansionMedium"
    )
    Metadata_Items_Jewels_JewelPassiveTreeExpansionSmall: MetadataItemsJewelsJewelPassiveTreeExpansionSmall = Field(
        ..., alias="Metadata/Items/Jewels/JewelPassiveTreeExpansionSmall"
    )


class Model(RootModel[ClusterJewelsSchema]):
    root: ClusterJewelsSchema
