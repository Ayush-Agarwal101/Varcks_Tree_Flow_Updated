class ActionValidator:
    def __init__(self, variables):
        self.variables = variables

    def validate(self, actions):
        valid = []
        all_functions = self._get_all_functions()

        for a in actions:

            if a.action == "add_producer":
                function = a.details.get("function")

                if not function or "." not in function:
                    continue

                valid.append(a)
                continue

            if a.action == "connect_variable":
                var = a.target
                fn = a.details.get("to_function")

                if not var:
                    continue
                if var not in self.variables:
                    continue

                if not any(fn in existing for existing in all_functions):
                    # mark for creation instead
                    a.action = "create_function"
                    valid.append(a)
                    continue

                valid.append(a)
                continue

            if a.action == "create_function":
                valid.append(a)
                continue

            valid.append(a)

        return valid

    def _get_all_functions(self):
        fns = set()

        for var in self.variables.values():
            for fn in var.used_by + var.produced_by:
                fns.add(fn.split(".")[-1])

        return fns