from core.llm_structured import StructuredLLM
from pydantic import BaseModel, RootModel
from typing import Literal, Dict

class OutputDecision(BaseModel):
    action: Literal["connect", "remove", "keep"]
    target_function: str | None = None
    reason: str | None = None

class BatchOutputDecision(RootModel[Dict[str, OutputDecision]]):
    pass

class UnusedOutputReasoner:
    """
    LLM-based unused output reasoning
    """

    def __init__(self, variables, registry):
        self.variables = variables
        self.registry = registry

        self.llm = StructuredLLM(
            provider="nvidia",
            model="meta/llama-3.3-70b-instruct"
        )

    # ----------------------------------------
    # MAIN ENTRY
    # ----------------------------------------
    def generate_actions(self, unused_vars):
        if not unused_vars:
            return []

        decisions = self._decide_batch(unused_vars)
        actions = []

        for var, decision in decisions.items():

            if var not in self.variables:
                continue

            if decision.action == "connect" and decision.target_function:
                actions.append({
                    "action": "connect_variable",
                    "target": var,
                    "details": {
                        "to_function": decision.target_function
                    }
                })

            elif decision.action == "remove":
                actions.append({
                    "action": "remove_variable",
                    "target": var,
                    "details": {}
                })

        return actions

    def _decide_batch(self, variables):
        registry_summary = self._build_registry_summary()
        var_list = "\n".join(variables)

        prompt = f"""
    You are analyzing a system of functions and variables.

UNUSED VARIABLES:
{var_list}

SYSTEM CONTEXT:
{registry_summary}

Task:
For EACH variable, decide:
- connect → and specify target function
- remove
- keep

Rules:
- DO NOT hallucinate unrealistic functions
- Prefer existing functions
- Be consistent with system domain

Return JSON:

{{
  "variable_name": {{
    "action": "connect" | "remove" | "keep",
    "target_function": "function_name_or_null",
    "reason": "optional explanation"
  }}
}}
"""
        try:
            result: BatchOutputDecision = self.llm.call(
                prompt=prompt,
                schema=BatchOutputDecision
            )

            return result.root

        except Exception:
            # fallback: no actions (safe)
            return {}

    # ----------------------------------------
    # REGISTRY SUMMARY
    # ----------------------------------------

    def _build_registry_summary(self):
        lines = []

        for var, data in list(self.registry.get("variables", {}).items())[:30]:
            producers = data.get("produced_by", [])
            lines.append(f"{var} → produced_by: {producers}")

        return "\n".join(lines)