# core/normalization/registry_builder.py

import os
import yaml
from typing import List
from .models import FunctionMeta, VariableMeta, Registry
from .basic_normalizer import normalize_variable, normalize_function_name


def build_registry(function_specs_dir: str) -> Registry:
    functions: List[FunctionMeta] = []
    variables = {}

    for root, _, files in os.walk(function_specs_dir):
        for file in files:
            if not file.endswith(".yaml"):
                continue

            path = os.path.join(root, file)

            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            file_path = data.get("file", "")

            for fn in data.get("functions", []):

                name = normalize_function_name(fn["name"])

                parameters = []
                for p in fn.get("parameters", []):
                    entity = p.get("entity", "unknown")
                    var_name = f"{entity}.{p['name']}"
                    var_name = normalize_variable(var_name)
                    parameters.append(var_name)

                produces = []
                for out in fn.get("produces", []):
                    produces.append(normalize_variable(out))

                meta = FunctionMeta(
                    file=file_path,
                    name=name,
                    parameters=parameters,
                    produces=produces,
                    description=fn.get("description", "")
                )

                functions.append(meta)

                # Build variable registry
                for var in parameters:
                    variables.setdefault(var, VariableMeta(name=var))
                    variables[var].consumed_by.append(f"{file_path}.{name}")

                for var in produces:
                    variables.setdefault(var, VariableMeta(name=var))
                    variables[var].produced_by.append(f"{file_path}.{name}")

    return Registry(functions=functions, variables=variables)