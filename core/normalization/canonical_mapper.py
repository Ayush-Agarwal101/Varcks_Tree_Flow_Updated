# core/normalization/canonical_mapper.py

from typing import Dict, List
from core.normalization.models import FunctionMeta
from core.normalization.basic_normalizer import normalize_variable

class CanonicalMapper:
    """
    Builds:
    - function_map: variant_function → canonical_function
    - variable_map: old_variable → canonical_variable
    - canonical_functions: new canonical functions created by LLM
    """

    def __init__(self):
        self.function_map: Dict[str, str] = {}
        self.variable_map: Dict[str, str] = {}
        self.canonical_functions: Dict[str, Dict] = {}

    # ---------------------------
    # SAFE CLUSTERS
    # ---------------------------

    def process_safe_clusters(self, safe_clusters: List[List[FunctionMeta]]):
        for cluster in safe_clusters:
            canonical_fn = cluster[0]
            canonical_id = f"{canonical_fn.file}.{canonical_fn.name}"

            for fn in cluster:
                fn_id = f"{fn.file}.{fn.name}"
                self.function_map[fn_id] = canonical_id

    # ---------------------------
    # AMBIGUOUS CLUSTERS
    # ---------------------------

    def process_ambiguous_clusters(
        self,
        ambiguous_clusters: List[List[FunctionMeta]],
        decisions: List[Dict]
    ):
        for cluster, decision in zip(ambiguous_clusters, decisions):

            canonical = decision.get("canonical", {})
            canonical_name = canonical.get("name")

            # detect if canonical exists in cluster
            matched_fn = None
            for fn in cluster:
                if fn.name == canonical_name:
                    matched_fn = fn
                    break

            # CASE 1: canonical exists
            if matched_fn:
                canonical_file = matched_fn.file

            # CASE 2: canonical is NEW (LLM created)
            else:
                canonical_file = self._choose_best_file(cluster, canonical)

                canonical_id = f"{canonical_file}.{canonical_name}"

                self.canonical_functions[canonical_id] = {
                    "name": canonical.get("name"),
                    "parameters": canonical.get("parameters", []),
                    "return_type": canonical.get("return_type", "unknown"),
                    "entity": canonical.get("entity", ""),
                    "produces": canonical.get("produces", []),
                    "description": canonical.get("description", "")
                }

            canonical_id = f"{canonical_file}.{canonical_name}"

            # map all functions → canonical
            for fn in cluster:
                fn_id = f"{fn.file}.{fn.name}"
                self.function_map[fn_id] = canonical_id

            # variable mappings
            mappings = decision.get("mappings", {})
            for old, new in mappings.items():

                # skip invalid mappings
                if not old or not new:
                    continue

                if "." not in old or "." not in new:
                    continue

                old_norm = normalize_variable(old)
                new_norm = normalize_variable(new)

                if old_norm != new_norm:
                    self.variable_map[old_norm] = new_norm

    # ---------------------------
    # FILE SELECTION LOGIC
    # ---------------------------

    def _choose_best_file(self, cluster: List[FunctionMeta], canonical: Dict) -> str:
        """
        Choose best file to place canonical function
        Heuristic:
        - prefer shorter path (core module)
        - fallback: first file
        """
        sorted_cluster = sorted(cluster, key=lambda fn: len(fn.file))
        return sorted_cluster[0].file

    # ---------------------------
    # FINAL OUTPUT
    # ---------------------------

    def finalize(self, all_functions: List[FunctionMeta]):
        for fn in all_functions:
            fn_id = f"{fn.file}.{fn.name}"
            if fn_id not in self.function_map:
                self.function_map[fn_id] = fn_id

    def get_function_map(self) -> Dict[str, str]:
        return self.function_map

    def get_variable_map(self) -> Dict[str, str]:
        return self.variable_map

    def get_canonical_functions(self) -> Dict[str, Dict]:
        return self.canonical_functions