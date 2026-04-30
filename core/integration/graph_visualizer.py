from graphviz import Digraph


class GraphVisualizer:
    """
    Generates visual graphs for:
    - Function flow
    - Variable flow (with issue highlighting)
    """

    def __init__(self, graph):
        self.graph = graph

    # ----------------------------------------
    # FUNCTION FLOW GRAPH
    # ----------------------------------------
    def render_function_graph(self, path="outputs/function_graph"):
        seen_nodes = set()
        dot = Digraph(comment="Function Flow")
        dot.attr(rankdir="LR")

        for fn, connections in self.graph.items():
            if fn not in seen_nodes:
                dot.node(fn, shape="box")
                seen_nodes.add(fn)

            for target in connections:
                dot.edge(fn, target)

        dot.render(path, format="png", cleanup=True)

    def render_broken_flows(self, variables, report, path):
        seen_nodes = set()

        dot = Digraph(comment="Broken Flows Only")
        dot.attr(rankdir="LR")

        unused = set(report.get("unused_outputs", []))

        multi_data = report.get("multiple_producers", {})
        print("[DEBUG multiple_producers]:", multi_data)

        multi = set()

        if isinstance(multi_data, dict):
            multi = set(multi_data.keys())

        elif isinstance(multi_data, list):
            for item in multi_data:
                if isinstance(item, str):
                    multi.add(item)
                elif isinstance(item, (list, tuple)) and len(item) > 0:
                    multi.add(item[0])

        missing = set(report.get("missing_producers", []))

        broken_vars = unused | multi | missing

        # LIMIT SIZE (important)
        for var in list(broken_vars)[:25]:

            if var not in variables:
                continue

            meta = variables[var]

            # COLOR
            if var in unused:
                color = "yellow"
            elif var in multi:
                color = "red"
            elif var in missing:
                color = "orange"
            else:
                color = "lightblue"

            # VARIABLE NODE
            if var not in seen_nodes:
                dot.node(var, shape="ellipse", style="filled", fillcolor=color)
                seen_nodes.add(var)

            # PRODUCERS
            for p in meta.produced_by:
                if p not in seen_nodes:
                    dot.node(p, shape="box")
                    seen_nodes.add(p)
                dot.edge(p, var)

            # CONSUMERS
            for u in meta.used_by:
                if u not in seen_nodes:
                    dot.node(u, shape="box")
                    seen_nodes.add(u)
                dot.edge(var, u)

        dot.render(path, format="png", cleanup=True)

    def render_variable_graph_labeled(self, variables, report, path):
        seen_nodes = set()
        dot = Digraph(comment="Variable Flow")
        dot.attr(rankdir="LR")

        unused = set(report.get("unused_outputs", []))

        multi_data = report.get("multiple_producers", {})
        print("[DEBUG multiple_producers]:", multi_data)

        multi = set()

        if isinstance(multi_data, dict):
            multi = set(multi_data.keys())

        elif isinstance(multi_data, list):
            for item in multi_data:
                if isinstance(item, str):
                    multi.add(item)
                elif isinstance(item, (list, tuple)) and len(item) > 0:
                    multi.add(item[0])

        for var, meta in variables.items():

            # COLOR
            if var in unused:
                color = "yellow"
            elif var in multi:
                color = "red"
            else:
                color = "lightblue"

            # VARIABLE NODE
            if var not in seen_nodes:
                dot.node(var, shape="ellipse", style="filled", fillcolor=color)
                seen_nodes.add(var)

            # PRODUCERS
            for fn in meta.produced_by:
                if fn not in seen_nodes:
                    dot.node(fn, shape="box")
                    seen_nodes.add(fn)
                dot.edge(fn, var)

            # CONSUMERS
            for fn in meta.used_by:
                if fn not in seen_nodes:
                    dot.node(fn, shape="box")
                    seen_nodes.add(fn)
                dot.edge(var, fn)

        dot.render(path, format="png", cleanup=True)

    def render_variable_graph(self, variables, report, path="outputs/variable_graph"):
        seen_nodes = set()

        dot = Digraph(comment="Chained Variable Flow")
        dot.attr(rankdir="LR")

        unused = set(report.get("unused_outputs", []))

        multi_data = report.get("multiple_producers", {})
        print("[DEBUG multiple_producers]:", multi_data)

        multi = set()

        if isinstance(multi_data, dict):
            multi = set(multi_data.keys())

        elif isinstance(multi_data, list):
            for item in multi_data:
                if isinstance(item, str):
                    multi.add(item)
                elif isinstance(item, (list, tuple)) and len(item) > 0:
                    multi.add(item[0])

        # -------------------------
        # ADD ALL NODES
        # -------------------------
        for var, meta in variables.items():

            # COLOR
            if var in unused:
                color = "yellow"
            elif var in multi:
                color = "red"
            else:
                color = "lightblue"

            # VARIABLE NODE
            if var not in seen_nodes:
                dot.node(var, shape="ellipse", style="filled", fillcolor=color)
                seen_nodes.add(var)

            # FUNCTION NODES
            for fn in meta.produced_by + meta.used_by:
                if fn not in seen_nodes:
                    dot.node(fn, shape="box")
                    seen_nodes.add(fn)

        # -------------------------
        # BUILD MAP FIRST
        # -------------------------
        producer_to_vars = {}
        for var, meta in variables.items():
            for p in meta.produced_by:
                producer_to_vars.setdefault(p, []).append(var)

        # -------------------------
        # CONNECT CHAINS
        # -------------------------
        for var, meta in variables.items():

            # producer → variable
            for producer in meta.produced_by:
                dot.edge(producer, var)

            # variable → consumer
            for consumer in meta.used_by:
                dot.edge(var, consumer)

                # chain forward
                for next_var in producer_to_vars.get(consumer, []):
                    dot.edge(consumer, next_var)

        dot.render(path, format="png", cleanup=True)

        # Yellow nodes -> unused