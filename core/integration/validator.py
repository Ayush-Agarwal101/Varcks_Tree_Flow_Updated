import re

def tokenize(name):
    return set(name.lower().split("_"))

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

                if not var or var not in self.variables:
                    continue

                if not fn:
                    continue

                # -------------------------
                # NORMALIZE FUNCTION NAME
                # -------------------------
                fn_name = re.split(r"[/.]", fn)[-1]
                if fn in all_functions:
                    if fn in self.variables[var].used_by:
                        continue

                    a.details["to_function"] = fn
                    valid.append(a)
                    continue

                # find matching system functions
                fn_tokens = set(re.split(r"[_.]", fn_name))

                matches = []

                for existing in all_functions:
                    existing_name = existing.split(".")[-1]
                    existing_tokens = set(existing_name.split("_"))

                    overlap = fn_tokens & existing_tokens

                    # require meaningful overlap (at least 1 strong token)
                    if len(overlap) >= 1 and len(existing_tokens) >= 2:
                        matches.append((existing, len(overlap)))

                if not matches:
                    print(f"[VALIDATOR DROP] No match for {fn}")
                    continue

                # -------------------------
                # PICK BEST MATCH
                # -------------------------
                def rank(item):
                    fn, overlap_score = item

                    score = overlap_score

                    if "backend" in fn:
                        score += 2
                    elif "frontend" in fn:
                        score += 1

                    return score

                matches = sorted(matches, key=rank, reverse=True)
                best_fn = matches[0][0]

                if best_fn in self.variables[var].used_by:
                    continue

                # overwrite with best match
                a.details["to_function"] = best_fn
                print(f"[VALIDATOR] {fn} → matched → {a.details['to_function']}")

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
                fns.add(fn)

        return fns