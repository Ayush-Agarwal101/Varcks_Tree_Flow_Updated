# core/integration/flow_reasoner.py

class FlowReasoner:
    """
    Advanced reasoning:
    - resolve multiple producers
    - detect and complete pipelines
    """

    def __init__(self, registry):
        self.registry = registry
        self.functions = registry.get("functions", {})
        self.variables = registry.get("variables", {})

    # ----------------------------------------
    # 1. MULTIPLE PRODUCER RESOLUTION
    # ----------------------------------------
    def resolve_producers(self):
        decisions = []

        for var, data in self.variables.items():
            producers = data.get("produced_by", [])

            if len(producers) <= 1:
                continue

            best = self._choose_best_producer(producers)

            decisions.append({
                "action": "keep_only_producer",
                "target": var,
                "details": {"function": best}
            })

        return decisions

    def _choose_best_producer(self, producers):
        """
        Priority:
        module > service > controller > frontend
        """

        def score(fn):
            fn = fn.lower()

            if "module" in fn:
                return 4
            if "service" in fn:
                return 3
            if "controller" in fn:
                return 2
            if "frontend" in fn:
                return 1
            return 0

        return sorted(producers, key=score, reverse=True)[0]

    # ----------------------------------------
    # 2. PIPELINE COMPLETION
    # ----------------------------------------
    def complete_pipelines(self):
        actions = []

        for fn, data in self.functions.items():

            produces = data.get("produces", [])

            for var in produces:

                # find if variable is consumed
                if not self._is_consumed(var):

                    next_fn = self._suggest_next_step(var)

                    if next_fn:
                        actions.append({
                            "action": "connect_variable",
                            "target": var,
                            "details": {"to_function": next_fn}
                        })

        return actions

    def _is_consumed(self, var):
        data = self.variables.get(var, {})
        return bool(data.get("used_by"))

    def _suggest_next_step(self, var):
        """
        Heuristic mapping
        """

        name = var.lower()

        if "order" in name:
            return "checkout"
        if "checkout" in name:
            return "payment"
        if "payment" in name:
            return "confirmation"
        if "product.list" in name:
            return "render_product_list"
        if "user" in name:
            return "render_user_profile"

        return None

    # ----------------------------------------
    # MAIN ENTRY
    # ----------------------------------------
    def generate_actions(self):
        actions = []

        actions.extend(self.resolve_producers())
        actions.extend(self.complete_pipelines())

        return actions