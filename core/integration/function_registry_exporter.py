import json
import os

class FunctionRegistryExporter:

    def __init__(self, variables):
        self.variables = variables

    def export(self, path="outputs/function_registry.json"):
        os.makedirs("outputs", exist_ok=True)

        functions = {}

        for var in self.variables.values():

            for fn in var.produced_by:
                functions.setdefault(fn, {
                    "produces": [],
                    "consumes": [],
                    "depends_on": set()
                })
                functions[fn]["produces"].append(var.key)

            for fn in var.used_by:
                functions.setdefault(fn, {
                    "produces": [],
                    "consumes": [],
                    "depends_on": set()
                })
                functions[fn]["consumes"].append(var.key)

        # build dependencies (imports-like)
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

        # convert sets to lists
        for fn in functions:
            functions[fn]["depends_on"] = list(functions[fn]["depends_on"])

        with open(path, "w") as f:
            json.dump(functions, f, indent=2)

        print(f"[FUNCTION REGISTRY] Saved → {path}")