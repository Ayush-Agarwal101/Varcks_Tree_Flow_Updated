# run_normalization.py

from core.normalization.registry_builder import build_registry
from core.normalization.clusterer import cluster_functions

if __name__ == "__main__":
    registry = build_registry("specs/raw/function_specs")

    print("\n=== FUNCTIONS ===")
    for fn in registry.functions[:5]:
        print(fn)

    print("\n=== VARIABLES ===")
    for k, v in list(registry.variables.items())[:10]:
        print(k, "→", v.produced_by, v.consumed_by)

    print("\n=== CLUSTERS ===")
    clusters = cluster_functions(registry.functions)

    print("\n=== SAFE CLUSTERS ===")
    for i, cluster in enumerate(clusters["safe"]):
        print(f"\nCluster {i}:")
        for fn in cluster:
            print(" -", fn.name)

    print("\n=== AMBIGUOUS CLUSTERS ===")
    for i, cluster in enumerate(clusters["ambiguous"]):
        print(f"\nCluster {i}:")
        for fn in cluster:
            print(" -", fn.name)