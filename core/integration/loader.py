# core/integration/loader.py

import os
import yaml
from typing import Dict
from .models import Variable
from core.normalization.basic_normalizer import normalize_variable


def get_backend_role(fn_name: str) -> str:
    name = fn_name.lower()

    if "controller" in name:
        return "controller"
    if "service" in name:
        return "service"
    if "module" in name:
        return "module"

    return "other"

class YAMLLoader:
    """
    Loads YAML function specs and builds variable graph.
    """

    def __init__(self):
        # key: entity.variable → Variable object
        self.variables: Dict[str, Variable] = {}

    # PUBLIC API

    def load_directory(self, directory: str):
        """
        Load all YAML files recursively.
        """
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".yaml") or file.endswith(".yml"):
                    filepath = os.path.join(root, file)
                    self._load_file(filepath)

        return self.variables

    # INTERNAL LOGIC

    def _get_or_create_variable(self, name: str, entity: str, var_type: str) -> Variable:
        raw_key = f"{entity}.{name}"
        norm_key = normalize_variable(raw_key)

        try:
            entity, name = norm_key.split(".")
        except ValueError:
            entity, name = "unknown", raw_key

        key = f"{entity}.{name}"

        if key not in self.variables:
            self.variables[key] = Variable(name, entity, var_type)

        return self.variables[key]

    def _load_file(self, filepath: str):
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        file_name = data.get("file") or os.path.relpath(filepath)
        file_name = file_name.replace("\\", "/").replace(".yaml", "").replace(".yml", "")

        functions = data.get("functions", [])

        for fn in functions:
            fn_name = fn.get("name")
            full_fn_name = f"{file_name}.{fn_name}"

            # HANDLE INPUTS (USED VARIABLES)
            for param in fn.get("parameters", []):
                name = param.get("name")
                entity = param.get("entity", "unknown")
                var_type = param.get("type", "unknown")

                if not name:
                    continue

                norm_key = normalize_variable(f"{entity}.{name}")

                try:
                    entity, name = norm_key.split(".")
                except ValueError:
                    continue

                var = self._get_or_create_variable(name, entity, var_type)
                var.add_consumer(full_fn_name)

            # HANDLE OUTPUTS (PRODUCED VARIABLES)
            produces = fn.get("produces", [])

            for prod in produces:
                norm_key = normalize_variable(prod)

                try:
                    entity, name = norm_key.split(".")
                except ValueError:
                    continue

                var_type = fn.get("return_type", "unknown")

                var = self._get_or_create_variable(name, entity, var_type)
                role = get_backend_role(full_fn_name)

                existing_roles = [
                    get_backend_role(p) for p in var.produced_by
                ]

                # PRIORITY: module > service > other

                if role == "module":
                    # module overrides everything
                    var.produced_by = [full_fn_name]

                elif role == "service":
                    if "module" not in existing_roles:
                        # replace lower priority
                        var.produced_by = [full_fn_name]

                elif role == "controller":
                    # never a final producer
                    pass

                else:
                    if not var.produced_by:
                        var.add_producer(full_fn_name)

