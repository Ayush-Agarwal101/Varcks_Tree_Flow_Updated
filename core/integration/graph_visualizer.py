# core/integration/graph_visualizer.py

from graphviz import Digraph
import os

def get_node_color(fn: str) -> str:
    fn = fn.lower()

    if "frontend" in fn:
        return "lightblue"

    if "controller" in fn:
        return "orange"

    if "service" in fn:
        return "yellow"

    if "module" in fn:
        return "green"

    if "backend" in fn:
        return "lightgrey"

    return "white"

class GraphVisualizer:

    def __init__(self, graph):
        self.graph = graph

    def build(self):
        dot = Digraph(comment="Function Dependency Graph")

        for fn, deps in self.graph.items():
            color = get_node_color(fn)

            dot.node(fn, style="filled", fillcolor=color)

            for dep in deps:
                dot.edge(fn, dep)

        return dot

    def render(self, output_path="function_graph"):
        dot = self.build()
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        dot.render(output_path, format="png", cleanup=True)
        print(f"[GRAPH] Saved to {output_path}.png")