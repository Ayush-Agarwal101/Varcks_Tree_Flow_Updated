# run_canonical_selector.py

from core.normalization.registry_builder import build_registry
from core.normalization.clusterer import cluster_functions
from core.normalization.canonical_selector import CanonicalSelector

if __name__ == "__main__":

    registry = build_registry("specs/raw/function_specs")
    clusters = cluster_functions(registry.functions)

    selector = CanonicalSelector()

    print("\n=== CANONICAL DECISIONS ===")

    for i, cluster in enumerate(clusters["ambiguous"]):

        print(f"\n--- Cluster {i} ---")

        decision = selector.select(cluster)

        print("\nCanonical:")
        print(decision.canonical)

        print("\nMappings:")
        print(decision.mappings)