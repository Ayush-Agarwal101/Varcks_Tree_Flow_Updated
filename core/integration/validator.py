class ActionValidator:
    def __init__(self, variables):
        self.variables = variables

    def validate(self, actions):
        valid = []
        all_functions = self._get_all_functions()

        for a in actions:

            # -------------------------
            # ADD PRODUCER
            # -------------------------
            if a.action == "add_producer":
                function = a.details.get("function")

                if not function or "." not in function:
                    continue

                valid.append(a)
                continue

            # -------------------------
            # CONNECT VARIABLE
            # -------------------------
            elif a.action == "connect_variable":
                var = a.target
                fn = a.details.get("to_function")

                if not var:
                    continue

                if var not in self.variables:
                    continue

                if not fn:
                    continue
                # strict match
                if fn not in all_functions:
                    continue

                valid.append(a)
                continue

            # -------------------------
            # CREATE FUNCTION
            # -------------------------
            elif a.action == "create_function":
                # prevent duplicate creation
                if a.target in self.variables:
                    continue

                valid.append(a)
                continue

            # -------------------------
            # KEEP ONLY PRODUCER (NEW)
            # -------------------------
            elif a.action == "keep_only_producer":
                var = a.target
                fn = a.details.get("function")

                if not var or not fn:
                    continue

                if var not in self.variables:
                    continue

                valid.append(a)
                continue

            # -------------------------
            # REMOVE PRODUCER (NEW)
            # -------------------------
            elif a.action == "remove_producer":
                var = a.target
                fn = a.details.get("function")

                if not var or not fn or "." not in fn:
                    continue

                valid.append(a)
                continue

            # -------------------------
            # DEFAULT
            # -------------------------
            else:
                valid.append(a)

        return valid

    def _get_all_functions(self):
        fns = set()

        for var in self.variables.values():
            for fn in var.used_by + var.produced_by:
                fns.add(fn.split(".")[-1])

        return fns