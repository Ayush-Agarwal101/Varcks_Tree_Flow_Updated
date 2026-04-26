import re
from typing import List
from .repair_engine import RepairAction

class SuggestionParser:
    """
    Converts suggest_improvement → structured executable actions
    """

    def parse(self, actions: List[RepairAction]) -> List[RepairAction]:
        parsed = []

        for a in actions:

            # ----------------------------------
            # PASS THROUGH NON-SUGGEST ACTIONS
            # ----------------------------------
            if a.action != "suggest_improvement":

                # block invalid create_function (variable targets)
                if a.action == "create_function" and "." in a.target:
                    continue

                if a.target:
                    parsed.append(a)
                continue

            reason = (a.reason or "").lower()
            target = a.target

            # ----------------------------------
            # CASE 1: variable → function connection
            # ----------------------------------
            match = re.search(r"(\w+\.\w+).*to (\w+)", reason)

            if match:
                var = match.group(1)
                fn = match.group(2)

                if var and fn:
                    parsed.append(RepairAction(
                        action="connect_variable",
                        target=var,
                        details={"to_function": fn},
                        reason=a.reason,
                        confidence=a.confidence
                    ))
                continue

            # ----------------------------------
            # CASE 2: flow continuation
            # e.g. "checkout should lead to payment"
            # ----------------------------------
            match = re.search(r"(\w+)\s+should\s+lead\s+to\s+(\w+)", reason)

            if match:
                src = match.group(1)
                fn = match.group(2)

                if src and fn:
                    parsed.append(RepairAction(
                        action="connect_variable",
                        target=src,
                        details={"to_function": fn},
                        reason=a.reason,
                        confidence=a.confidence
                    ))
                continue

            # ----------------------------------
            # CASE 3: function-level suggestion
            # ----------------------------------
            if target and "/" in target:
                fn_name = target.split("/")[-1]
                continue

            # ----------------------------------
            # CASE 4: create function (last resort)
            # ----------------------------------
            if target and any(k in reason for k in ["create", "missing", "not exist"]):

                # avoid variable misuse
                if "." in target:
                    continue

                parsed.append(RepairAction(
                    action="create_function",
                    target=target,
                    details={"description": a.reason},
                    reason=a.reason,
                    confidence=a.confidence
                ))
                continue

            # ----------------------------------
            # IGNORE weak suggestions
            # ----------------------------------
            # do NOT pass raw suggest_improvement
            continue

        return parsed