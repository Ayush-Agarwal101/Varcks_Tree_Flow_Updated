import json
import os
from core.integration.function_schema import FunctionSchema

class SystemRegistryBuilder:
    """
    Builds unified registry:
    {
      functions: {},
      variables: {}
    }
    """

    def __init__(self, variables):
        self.variables = variables

    # ----------------------------------------
    # BUILD FULL REGISTRY
    # ----------------------------------------
    def build(self):
        functions = self._build_functions()
        variables = self._build_variables()

        return {
            "functions": functions,
            "variables": variables
        }

    # ----------------------------------------
    # BUILD VARIABLES
    # ----------------------------------------
    def _build_variables(self):
        variables = {}

        for key, var in self.variables.items():
            variables[key] = {
                "produced_by": var.produced_by,
                "used_by": var.used_by,
                "type": var.type
            }

        return variables

    # ----------------------------------------
    # BUILD FUNCTIONS (SINGLE SOURCE OF TRUTH)
    # ----------------------------------------
    def _build_functions(self):
        functions = {}

        for var in self.variables.values():

            # -------------------------
            # PRODUCERS → outputs
            # -------------------------
            for fn in var.produced_by:

                if fn not in functions:
                    functions[fn] = FunctionSchema(
                        name=fn.split(".")[-1],
                        full_path=fn,
                    ).model_dump()

                    functions[fn]["produces"] = []
                    functions[fn]["consumes"] = []
                    functions[fn]["depends_on"] = set()

                if var.key not in functions[fn]["produces"]:
                    functions[fn]["produces"].append(var.key)

                if var.key not in functions[fn]["outputs"]:
                    functions[fn]["outputs"].append(var.key)

            # -------------------------
            # CONSUMERS → inputs
            # -------------------------
            for fn in var.used_by:

                if fn not in functions:
                    functions[fn] = FunctionSchema(
                        name=fn.split(".")[-1],
                        full_path=fn,
                    ).model_dump()

                    functions[fn]["produces"] = []
                    functions[fn]["consumes"] = []
                    functions[fn]["depends_on"] = set()

                if var.key not in functions[fn]["consumes"]:
                    functions[fn]["consumes"].append(var.key)

                if var.key not in functions[fn]["inputs"]:
                    functions[fn]["inputs"].append(var.key)

        # -------------------------
        # BUILD DEPENDENCIES
        # -------------------------
        for var in self.variables.values():
            for producer in var.produced_by:
                for consumer in var.used_by:

                    if producer == consumer:
                        continue

                    if consumer not in functions:
                        functions[consumer] = FunctionSchema(
                            name=consumer.split(".")[-1],
                            full_path=consumer,
                        ).model_dump()

                        functions[consumer]["produces"] = []
                        functions[consumer]["consumes"] = []
                        functions[consumer]["depends_on"] = set()

                    functions[consumer]["depends_on"].add(producer)

        # -------------------------
        # FINALIZE
        # -------------------------
        for fn in functions:
            functions[fn]["depends_on"] = list(functions[fn]["depends_on"])

            usage = len(functions[fn]["inputs"]) + len(functions[fn]["outputs"])
            functions[fn]["usage_count"] = usage

        return functions

    # ----------------------------------------
    # EXPORT FULL REGISTRY
    # ----------------------------------------
    def save(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)

        data = self.build()

        with open(path, "w") as f:
            json.dump(data, f, indent=2)

        print(f"[SYSTEM REGISTRY] Saved → {path}")

    # ----------------------------------------
    # EXPORT ONLY FUNCTIONS (REPLACES OLD FILE)
    # ----------------------------------------
    def save_functions(self, path="outputs/function_registry.json"):
        os.makedirs(os.path.dirname(path), exist_ok=True)

        functions = self._build_functions()

        with open(path, "w") as f:
            json.dump(functions, f, indent=2)

        print(f"[FUNCTION REGISTRY] Saved → {path}")