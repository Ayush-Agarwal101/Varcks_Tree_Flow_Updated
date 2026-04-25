# core/integration/repair_engine.py

from typing import Dict, List
from core.llm_structured import StructuredLLM
from pydantic import BaseModel
import re
import json

# SCHEMAS
class RepairAction(BaseModel):
    action: str   # "add_producer" | "map_variable" | "change_type"
    target: str
    details: Dict
    reason: str | None = None
    confidence: float | None = None

class RepairPlan(BaseModel):
    actions: List[RepairAction]

# ENGINE
class RepairEngine:

    def __init__(self, variables = None):
        self.llm = StructuredLLM(provider="nvidia", model="meta/llama-3.3-70b-instruct")
        self.variables = variables

    # ---------------------------
    # HELPERS
    # ---------------------------

    def _extract_function_names(self) -> set:
        """
        Collect existing function names from variable graph.
        """
        fn_names = set()

        if hasattr(self, "variables") and self.variables:
            for var in self.variables.values():
                for fn in var.used_by + var.produced_by:
                    fn_names.add(fn.split(".")[-1].lower())

        return fn_names

    def _filter_actions(self, actions):
        """
        Remove low-value / hallucinated suggestions.
        """
        valid_functions = self._extract_function_names()
        filtered = []

        for a in actions:

            if a.action != "suggest_improvement":
                filtered.append(a)
                continue

            reason = (a.reason or "").lower()

            confidence = 0.5  # base

            if "should be passed to" in reason:
                confidence += 0.2

            if "create_new" in (a.details or {}):
                confidence -= 0.2

            a.confidence = round(confidence, 2)

            # remove weak suggestions
            if any(x in reason for x in [
                "consider removing",
                "consider renaming"
            ]):
                continue

            match = re.search(r"to (\w+)\s*function", reason)
            target_fn = match.group(1) if match else None

            # if function doesn't exist → mark as create_new
            if target_fn and target_fn not in valid_functions:
                a.details = a.details or {}
                a.details["create_new"] = True

            filtered.append(a)

        return filtered

    def _group_by_entity(self, actions):
        """
        Group related variables (e.g., bakery_item.id/name/price)
        but preserve field-level detail.
        """
        grouped = {}
        result = []

        for a in actions:
            if "." not in a.target:
                result.append(a)
                continue

            entity, _ = a.target.split(".", 1)

            grouped.setdefault(entity, []).append(a)

        for entity, group in grouped.items():

            if len(group) == 1:
                result.append(group[0])
                continue

            merged = RepairAction(
                action="suggest_improvement",
                target=entity,
                details={
                    "fields": [a.target for a in group],
                    "field_reasons": {
                        a.target: a.reason for a in group if a.reason
                    },
                    "suggestion": "Connect or create function consuming full entity"
                },
                reason=f"{entity} fields are unused and likely belong together in a consumer function"
            )

            result.append(merged)

        return result

    # MAIN ENTRY
    def generate_plan(self, report: Dict, variables=None, system_registry=None) -> RepairPlan:
        """
        Generate repair plan based on integration report.
        """
        if variables is not None:
            self.variables = variables

        system_prompt = """
You are an expert system architect.

You are given a system integration report.

Your job is NOT ONLY to fix issues, but also to suggest improvements.

Allowed actions:

1. add_producer → fix missing variable producer
2. map_variable → normalize variable naming
3. change_type → fix type inconsistency

4. suggest_improvement → suggest architectural or flow improvement

For suggest_improvement:

You MUST:

1. Identify WHERE the variable should flow next
2. Suggest a specific function or type of function
3. If no such function exists → suggest creating one

DO NOT:
- Suggest vague targets like "details", "data", "info"
- Suggest renaming unless clearly necessary

GOOD examples:
- "order.id should be passed to checkout function"
- "product.list should be consumed by frontend render function"
- "user.profile should be used in profile display"

BAD examples:
- "connect to details"
- "rename to something better"

Rules:
- Be minimal and precise
- Prefer improving flow over adding new variables
- Avoid unnecessary changes

Return ONLY JSON in this format:

{
  "actions": [
    {
      "action": "...",
      "target": "...",
      "details": {},
      "reason": "..."
    }
  ]
}
"""
        registry_text = json.dumps(system_registry, indent=2)  # limit size
        user_prompt = f"""
        SYSTEM REPORT:
        {report}

        SYSTEM REGISTRY (SOURCE OF TRUTH):
        {registry_text}

        IMPORTANT:
        - The SYSTEM REGISTRY is the COMPLETE and FINAL representation of the system.
        - All function names and variables MUST come from this registry.

        STRICT RULES:
        1. ONLY use function names present in SYSTEM REGISTRY.
        2. DO NOT invent function names.
        3. If no suitable function exists → then suggest creating one.
        4. Always use exact variable names (entity.variable format).
        5. Prefer connecting existing functions over creating new ones.

        VARIABLE GRAPH SUMMARY:
        - Variables have producers and consumers
        - Some variables are unused or inconsistently connected

        YOUR TASK:

        1. Fix Issues:
           - Missing producers
           - Multiple producers
           - Type conflicts

        2. Improve Flow:
           - Connect outputs to correct consumers
           - Ensure logical flow between functions

        3. For UNUSED OUTPUTS:
           For each variable:
           - Decide:
             a) Should it flow into an existing function?
             b) Is it a final output?
             c) Should it be removed?

        4. For MULTIPLE PRODUCERS:
           - Prefer: module > service > controller
           - Suggest removing or redirecting weaker producers

        5. Detect Missing Steps:
           - Identify broken chains (e.g., create → ??? → render)
           - Suggest intermediate functions ONLY if necessary

        CRITICAL:
        - Always reference REAL functions from registry
        - Avoid vague names like "data", "details", "info"
        - Be specific and minimal

        GOOD EXAMPLES:
        - "order.id should be passed to checkout"
        - "product.list should be consumed by render_products"
        - "user.profile should be used in profile_view"

        BAD EXAMPLES:
        - "connect to details"
        - "send to data handler"
        - "improve naming"

        OUTPUT:
        Return structured JSON actions only.
        """

        raw = self.llm.call(
            prompt=system_prompt + "\n\n" + user_prompt,
            schema=dict  # accept raw dict first
        )

        # 🔧 normalize structure
        if "actions" in raw:
            plan = RepairPlan(**raw)

        elif "repair_plan" in raw and "actions" in raw["repair_plan"]:
            plan = RepairPlan(**raw["repair_plan"])

        else:
            plan = RepairPlan(actions=[])

        # APPLY FILTER + GROUPING
        plan = RepairPlan(actions=self._filter_actions(plan.actions))
        plan = RepairPlan(actions=self._group_by_entity(plan.actions))

        return plan