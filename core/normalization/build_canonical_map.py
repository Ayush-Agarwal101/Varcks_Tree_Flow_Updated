# core/normalization/build_canonical_map.py

from core.normalization.registry_builder import build_registry
from core.normalization.clusterer import cluster_functions
from core.normalization.canonical_selector import CanonicalSelector
from core.normalization.canonical_mapper import CanonicalMapper


def build_canonical_maps(specs_dir: str):
    registry = build_registry(specs_dir)
    clusters = cluster_functions(registry.functions)

    selector = CanonicalSelector()

    decisions = []
    for cluster in clusters["ambiguous"]:
        decision = selector.select(cluster)
        decisions.append(decision.dict())

    mapper = CanonicalMapper()

    mapper.process_safe_clusters(clusters["safe"])
    mapper.process_ambiguous_clusters(clusters["ambiguous"], decisions)

    mapper.finalize(registry.functions)

    return {
        "function_map": mapper.get_function_map(),
        "variable_map": mapper.get_variable_map(),
        "canonical_functions": mapper.get_canonical_functions(),
        "decisions": decisions,
        "clusters": clusters["ambiguous"]
    }