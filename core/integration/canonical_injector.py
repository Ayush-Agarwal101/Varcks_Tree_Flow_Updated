# core/integration/canonical_injector.py

import os
import yaml

class CanonicalInjector:
    """
    Injects new canonical functions into correct YAML files
    """

    def __init__(self, yaml_dir, canonical_functions):
        self.yaml_dir = yaml_dir
        self.canonical_functions = canonical_functions

    def inject(self):
        for canonical_id, fn_data in self.canonical_functions.items():

            file_path, fn_name = canonical_id.rsplit(".", 1)

            yaml_path = os.path.join(self.yaml_dir, file_path + ".yaml")

            if not os.path.exists(yaml_path):
                print(f"[WARN] Missing file for canonical function: {canonical_id}")
                continue

            with open(yaml_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            functions = data.get("functions", [])

            # prevent duplicate insertion
            if any(f.get("name") == fn_name for f in functions):
                continue

            new_fn = {
                "name": fn_data.get("name"),
                "parameters": fn_data.get("parameters", []),
                "return_type": fn_data.get("return_type", "unknown"),
                "entity": fn_data.get("entity", ""),
                "produces": fn_data.get("produces", []),
                "description": fn_data.get("description", "")
            }

            functions.append(new_fn)
            data["functions"] = functions

            with open(yaml_path, "w", encoding="utf-8") as f:
                yaml.dump(data, f, sort_keys=False)

            print(f"[INJECTED] {fn_name} -> {file_path}")