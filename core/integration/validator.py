class ActionValidator:
    """
    Validates parsed actions against actual system graph
    """

    def __init__(self, variables):
        self.variables = variables

    def validate(self, actions):
        valid = []

        all_functions = self._get_all_functions()

        for a in actions:

            if a.action == "connect_variable":
                var = a.target
                fn = a.details.get("to_function")

                # check variable exists
                if var not in self.variables:
                    continue

                # check function exists
                if fn not in all_functions:
                    # mark for creation instead
                    a.action = "create_function"
                    valid.append(a)
                    continue

                valid.append(a)

            elif a.action == "create_function":
                valid.append(a)

            else:
                valid.append(a)

        return valid

    def _get_all_functions(self):
        fns = set()

        for var in self.variables.values():
            for fn in var.used_by + var.produced_by:
                fns.add(fn.split(".")[-1])

        return fns