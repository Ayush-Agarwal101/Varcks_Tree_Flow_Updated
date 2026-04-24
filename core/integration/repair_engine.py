# core/integration/repair_engine.py

from typing import Dict, List
from core.llm_structured import StructuredLLM
from pydantic import BaseModel

# ---------------------------
# SCHEMAS
# ---------------------------

class RepairAction(BaseModel):
    action: str   # "add_producer" | "map_variable" | "change_type"
    target: str
    details: Dict


class RepairPlan(BaseModel):
    actions: List[RepairAction]


# ---------------------------
# ENGINE
# ---------------------------

class RepairEngine:

    def __init__(self):
        self.llm = StructuredLLM(provider="nvidia", model="meta/llama-3.3-70b-instruct")

    # ---------------------------
    # MAIN ENTRY
    # ---------------------------

    def generate_plan(self, report: Dict) -> RepairPlan:
        """
        Generate repair plan based on integration report.
        """

        system_prompt = """
You are an expert software integration engine.

You are given a system analysis report with issues.

Your job is to generate a structured repair plan.

Allowed actions:

1. add_producer:
   - Add a function that produces a missing variable

2. map_variable:
   - Map one variable to another (e.g., uid → user.user_id)

3. change_type:
   - Fix type inconsistencies

Rules:
- Be minimal. Do NOT rewrite entire system.
- Only fix the exact issues.
- Prefer mapping over creating new variables.
- Keep naming consistent.

Return ONLY valid JSON.
"""

        user_prompt = f"""
SYSTEM REPORT:
{report}

Generate repair plan.
"""

        return self.llm.call(
            prompt=system_prompt + "\n\n" + user_prompt,
            schema=RepairPlan
        )