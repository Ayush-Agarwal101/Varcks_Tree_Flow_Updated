# core/integration/function_schema.py

from pydantic import BaseModel, Field, RootModel
from typing import List, Dict


class FunctionSchema(BaseModel):
    name: str
    full_path: str

    inputs: List[str] = Field(default_factory=list)
    outputs: List[str] = Field(default_factory=list)

    description: str = ""

    usage_count: int = 0
    is_locked: bool = False

class FunctionDescription(BaseModel):
    description: str

class BatchFunctionDescriptions(RootModel[Dict[str, FunctionDescription]]):
    pass