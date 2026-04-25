# core/integration/canonical_rewriter.py

import os
import yaml
from typing import Dict, List
from core.normalization.basic_normalizer import normalize_variable

class CanonicalRewriter:
    """
    Rewrites YAML files using:
    - function_map (variant → canonical)
    - variable_map (old → new)
    """

    def __init__(
        self,
        yaml_dir: str,
        function_map: Dict[str, str],
        variable_map: Dict[str, str]
    ):
        self.yaml_dir = yaml_dir
        self.function_map = function_map
        self.variable_map = variable_map

    # PUBLIC API

    def rewrite_all(self):
        for root, _, files in os.walk(self.yaml_dir):
            for file in files:
                if file.endswith(".yaml"):
                    path = os.path.join(root, file)
                    self._rewrite_file(path)

    # FILE REWRITE

    def _rewrite_file(self, filepath: str):
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        file_path = data.get("file", "").replace("\\","/")
        functions = data.get("functions", [])

        new_functions = []
        seen = set()

        for fn in functions:
            original_id = f"{file_path}.{fn['name']}"
            canonical_id = self.function_map.get(original_id, original_id)

            canonical_name = canonical_id.split(".")[-1]

            # rename function
            fn["name"] = canonical_name

            # avoid duplicate canonical definitions in same file
            if canonical_id in seen:
                continue
            seen.add(canonical_id)

            rewritten_fn = self._rewrite_function(fn)
            new_functions.append(rewritten_fn)

        if not new_functions:
            return

        data["functions"] = new_functions

        with open(filepath, "w", encoding="utf-8") as f:
            yaml.dump(data, f, sort_keys=False)

    # FUNCTION REWRITE

    def _rewrite_function(self, fn: Dict) -> Dict:
        new_params = []

        for p in fn.get("parameters", []):
            name = p.get("name")
            entity = p.get("entity", "unknown")

            key = f"{entity}.{name}"
            norm_key = normalize_variable(key)
            mapped = self.variable_map.get(norm_key, norm_key)

            try:
                new_entity, new_name = mapped.split(".")
            except ValueError:
                new_entity, new_name = entity, name

            new_params.append({
                "name": new_name,
                "type": p.get("type", "unknown"),
                "entity": new_entity
            })

        new_produces = []

        for prod in fn.get("produces", []):
            norm_prod = normalize_variable(prod)
            mapped = self.variable_map.get(norm_prod, norm_prod)
            new_produces.append(mapped)

        if not new_produces:
            entity = fn.get("entity", "unknown")
            new_produces.append(f"{entity}.result")

        return {
            "name": fn["name"],
            "parameters": new_params,
            "return_type": fn.get("return_type", "unknown"),
            "entity": fn.get("entity", ""),
            "produces": new_produces,
            "description": fn.get("description", "")
        }