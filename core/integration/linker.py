# core/integration/linker.py

from typing import Dict, List
from .models import Variable
from core.normalization.basic_normalizer import normalize_variable

class IntegrationLinker:
    """
    Builds links between functions based on shared variables.
    """

    def __init__(self, variables: Dict[str, Variable]):
        self.variables = variables

    # 1. Build variable-level links

    def build_variable_links(self) -> List[Dict]:
        """
        Create links:
        producer → consumer for each variable
        """
        links = []

        for var in self.variables.values():
            for producer in var.produced_by:
                for consumer in var.used_by:
                    var_key = normalize_variable(f"{var.entity}.{var.name}")

                    links.append({
                        "variable": var_key,
                        "from": producer,
                        "to": consumer
                    })

        return links

    # 2. Build function dependency graph

    def build_function_graph(self) -> Dict[str, List[str]]:
        """
        Build adjacency list:
        function → list of dependent functions
        """
        graph: Dict[str, List[str]] = {}

        for var in self.variables.values():
            var_key = normalize_variable(f"{var.entity}.{var.name}")

            for producer in var.produced_by:
                graph.setdefault(producer, [])

                for consumer in var.used_by:
                    if consumer != producer and consumer not in graph[producer]:
                        graph[producer].append(consumer)

        return graph

    # 3. Reverse graph (who depends on me)

    def build_reverse_graph(self) -> Dict[str, List[str]]:
        """
        Build reverse dependencies:
        function → who produces inputs for it
        """
        reverse_graph: Dict[str, List[str]] = {}

        for var in self.variables.values():
            for consumer in var.used_by:
                reverse_graph.setdefault(consumer, [])

                for producer in var.produced_by:
                    if producer != consumer and producer not in reverse_graph[consumer]:
                        reverse_graph[consumer].append(producer)

        return reverse_graph

    # 4. Find entry points

    def find_entry_points(self) -> List[str]:
        """
        Functions that do not depend on any other functions
        """
        reverse_graph = self.build_reverse_graph()

        entry_points = []

        for fn, producers in reverse_graph.items():
            if not producers:
                entry_points.append(fn)

        return entry_points

    # 5. Find terminal nodes

    def find_terminal_nodes(self) -> List[str]:
        """
        Functions that are not used by any other functions
        """
        graph = self.build_function_graph()

        terminals = []

        for fn, consumers in graph.items():
            if not consumers:
                terminals.append(fn)

        return terminals