# core/integration/loader.py

import os
import yaml
from typing import Dict
from .models import Variable

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
        key = f"{entity}.{name}"

        if key not in self.variables:
            self.variables[key] = Variable(name, entity, var_type)

        return self.variables[key]

    def _load_file(self, filepath: str):
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        file_name = data.get("file", filepath)

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

                var = self._get_or_create_variable(name, entity, var_type)
                var.add_consumer(full_fn_name)

            # HANDLE OUTPUTS (PRODUCED VARIABLES)
            produces = fn.get("produces", [])

            for prod in produces:
                try:
                    entity, name = prod.split(".")
                except ValueError:
                    # skip malformed entries
                    continue

                var_type = fn.get("return_type", "unknown")

                var = self._get_or_create_variable(name, entity, var_type)
                var.add_producer(full_fn_name)