# core/integration/detectors.py

from typing import Dict, List, Tuple
from .models import Variable

class IntegrationDetectors:
    """
    Runs various checks on variable graph.
    """

    def __init__(self, variables: Dict[str, Variable]):
        self.variables = variables

    # 1. Missing Producers

    def detect_missing_producers(self) -> List[str]:
        """
        Variable is used but never produced.
        """
        missing = []

        for var in self.variables.values():
            if var.used_by and not var.produced_by:
                missing.append(var.key)

        return missing

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

    def detect_unused_outputs(self) -> List[str]:
        """
        Variable is produced but never used.
        """
        unused = []

        for var in self.variables.values():
            if var.produced_by and not var.used_by:
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
            "unused_outputs": self.detect_unused_outputs()
        }