# core/schemas.py

from pydantic import BaseModel, field_validator
from typing import Optional, List

# Node Decision Schema (Single Choice Mode)
class NodeDecision(BaseModel):
    choice: int
    rationale: str
    purpose: str
    # internal fields
    choice_index: Optional[int] = None
    choice_name: Optional[str] = None

    @field_validator("choice")
    def validate_choice(cls, v):
        if not isinstance(v, int):
            raise ValueError("choice must be an integer")
        return v

    @field_validator("rationale", "purpose")
    def non_empty(cls, v):
        if not v or not v.strip():
            return "Not provided"
        return v.strip()

class PruneDecision(BaseModel):
    decision: str
    reason: str

    @field_validator("decision")
    def validate_decision(cls, v):
        if v.upper() not in ("KEEP", "PRUNE"):
            raise ValueError("decision must be KEEP or PRUNE")
        return v.upper()