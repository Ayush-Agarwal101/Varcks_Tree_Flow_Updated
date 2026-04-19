# core/normalization/models.py

from dataclasses import dataclass, field
from typing import List


@dataclass
class FunctionMeta:
    file: str
    name: str
    parameters: List[str]
    produces: List[str]
    description: str


@dataclass
class VariableMeta:
    name: str  # entity.variable
    produced_by: List[str] = field(default_factory=list)
    consumed_by: List[str] = field(default_factory=list)


@dataclass
class Registry:
    functions: List[FunctionMeta]
    variables: dict  # key: entity.variable -> VariableMeta