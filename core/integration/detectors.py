# core/integration/detectors.py

from typing import Dict, List, Tuple
from .models import Variable

class IntegrationDetectors:
    """
    Runs various checks on variable graph.
    """

    def __init__(self, variables: Dict[str, Variable]):
        self.variables = variables

    def detect_producer_priority_conflicts(self):
        """
        Detect cases where multiple producers exist,
        but some are lower quality (controller > service > module)
        """
        conflicts = []

        def get_role(fn):
            fn = fn.lower()
            if "module" in fn:
                return 3
            if "service" in fn:
                return 2
            if "controller" in fn:
                return 1
            return 0

        for var in self.variables.values():
            if len(var.produced_by) <= 1:
                continue

            ranked = sorted(var.produced_by, key=get_role, reverse=True)

            conflicts.append({
                "variable": var.key,
                "producers": var.produced_by,
                "preferred": ranked[0]
            })

        return conflicts

    # 1. Missing Producers

    def detect_missing_producers(self) -> List[str]:
        """
        Variable is used but never produced, AND is not likely an external input.
        """
        missing = []

        for var in self.variables.values():

            # must be used but not produced
            if not (var.used_by and not var.produced_by):
                continue

            # ignore likely input variables
            if self._is_likely_input(var):
                continue

            missing.append(var.key)

        return missing

    def _is_likely_input(self, var: Variable) -> bool:
        """
        Heuristic to filter out external inputs
        """

        name = var.name.lower()

        input_keywords = {
            "id", "ids",
            "name", "username", "email", "password",
            "query", "limit", "page", "offset",
            "filter", "sort",
            "category", "type",
            "data", "details"
        }

        # common input-style variables
        if name in input_keywords:
            return True

        # used but never produced anywhere → likely input
        if not var.produced_by and len(var.used_by) >= 1:
            return True

        return False

    # 2. Multiple Producers

    def detect_multiple_producers(self) -> List[Tuple[str, List[str]]]:
        """
        Variable produced by more than one function.
        """
        conflicts = []

        for var in self.variables.values():
            if len(var.produced_by) > 1:
                conflicts.append((var.key, var.produced_by))

        return conflicts

    # 3. Type Conflicts

    def detect_type_conflicts(self) -> List[Tuple[str, List[str]]]:
        """
        Same variable appears with multiple types.
        """
        type_map = {}

        for var in self.variables.values():
            key = var.key

            if key not in type_map:
                type_map[key] = set()

            type_map[key].add(var.type)

        conflicts = []

        for key, types in type_map.items():
            if len(types) > 1:
                conflicts.append((key, list(types)))

        return conflicts

    # 4. Unused Outputs

    def _is_terminal_output(self, var: Variable) -> bool:
        name = var.name.lower()

        terminal_keywords = {
            "html", "content", "rendered",
            "result", "response", "output",
            "view", "page",
            "profile", "list", "data",
            "status"
        }

        # obvious terminal names
        if any(k in name for k in terminal_keywords):
            return True

        # produced but only used by frontend or nowhere
        if var.produced_by:
            for fn in var.produced_by:
                fn_lower = fn.lower()

                if any(k in fn_lower for k in ["frontend", "render", "view"]):
                    return True

        return False

    def detect_unused_outputs(self) -> List[str]:
        """
        Variable is produced but never used,
        AND is not a terminal/output variable.
        """
        unused = []

        for var in self.variables.values():

            if not (var.produced_by and not var.used_by):
                continue

            # ignore valid terminal outputs
            if self._is_terminal_output(var):
                continue

            unused.append(var.key)

        return unused

    # 5. Summary

    def run_all_checks(self) -> Dict:
        """
        Run all detectors and return structured report.
        """
        return {
            "missing_producers": self.detect_missing_producers(),
            "multiple_producers": self.detect_multiple_producers(),
            "type_conflicts": self.detect_type_conflicts(),
            "unused_outputs": self.detect_unused_outputs(),
            "producer_priority_conflicts": self.detect_producer_priority_conflicts()
        }