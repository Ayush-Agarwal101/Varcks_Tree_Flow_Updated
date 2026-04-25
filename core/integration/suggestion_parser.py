import re
from typing import List
from .repair_engine import RepairAction

class SuggestionParser:
    """
    Converts suggest_improvement → structured actions
    """

    def parse(self, actions: List[RepairAction]) -> List[RepairAction]:
        parsed = []

        for a in actions:

            if a.action != "suggest_improvement":
                parsed.append(a)
                continue

            reason = (a.reason or "").lower()

            # ------------------------
            # CASE 1: connect_variable
            # ------------------------
            match = re.search(r"(\w+\.\w+) should be passed to (\w+)", reason)

            if match:
                variable = match.group(1)
                target_fn = match.group(2)

                parsed.append(RepairAction(
                    action="connect_variable",
                    target=variable,
                    details={
                        "to_function": target_fn
                    },
                    reason=a.reason,
                    confidence=a.confidence
                ))
                continue

            # ------------------------
            # CASE 2: create_function
            # ------------------------
            if "create" in reason or "missing" in reason:
                parsed.append(RepairAction(
                    action="create_function",
                    target=a.target,
                    details={
                        "description": a.reason
                    },
                    reason=a.reason,
                    confidence=a.confidence
                ))
                continue

            # fallback
            parsed.append(a)

        return parsed