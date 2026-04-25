import json
import os

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

    def build(self):
        functions = {}
        variables = {}

        # -------------------------
        # Build variable registry
        # -------------------------
        for key, var in self.variables.items():
            variables[key] = {
                "produced_by": var.produced_by,
                "used_by": var.used_by,
                "type": var.type
            }

        # -------------------------
        # Build function registry
        # -------------------------
        for var in self.variables.values():

            # PRODUCERS
            for fn in var.produced_by:
                functions.setdefault(fn, {
                    "produces": [],
                    "consumes": [],
                    "depends_on": set()
                })
                if var.key not in functions[fn]["produces"]:
                    functions[fn]["produces"].append(var.key)

            # CONSUMERS
            for fn in var.used_by:
                functions.setdefault(fn, {
                    "produces": [],
                    "consumes": [],
                    "depends_on": set()
                })
                if var.key not in functions[fn]["consumes"]:
                    functions[fn]["consumes"].append(var.key)

        # -------------------------
        # Build dependencies
        # -------------------------
        for var in self.variables.values():
            for producer in var.produced_by:
                for consumer in var.used_by:

                    if producer == consumer:
                        continue

                    functions.setdefault(consumer, {
                        "produces": [],
                        "consumes": [],
                        "depends_on": set()
                    })

                    functions[consumer]["depends_on"].add(producer)

        # convert sets → list
        for fn in functions:
            functions[fn]["depends_on"] = list(functions[fn]["depends_on"])

        return {
            "functions": functions,
            "variables": variables
        }

    def save(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)

        data = self.build()

        with open(path, "w") as f:
            json.dump(data, f, indent=2)

        print(f"[SYSTEM REGISTRY] Saved → {path}")