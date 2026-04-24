# core/normalization/clusterer.py

from collections import defaultdict
from difflib import SequenceMatcher


def similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()

def is_safe_duplicate(cluster, desc_threshold=0.75):
    base = cluster[0]

    for fn in cluster[1:]:

        # Name match
        if fn.name != base.name:
            return False

        # Parameters match
        if set(fn.parameters) != set(base.parameters):
            return False

        # Prevent empty produces merge
        if fn.produces and base.produces:
            if set(fn.produces) != set(base.produces):
                return False

        if set(fn.produces) != set(base.produces):
            return False

        # Pairwise description similarity (better)
        desc_scores = [
            similarity(fn.description, other.description)
            for other in cluster if other != fn
        ]

        if desc_scores and max(desc_scores) < desc_threshold:
            return False

    return True

def get_context(file_path: str) -> str:
    path = file_path.lower()

    # backend roles (highest priority)
    if "controller" in path:
        return "backend_controller"

    if "service" in path:
        return "backend_service"

    if "module" in path:
        return "backend_module"

    # frontend roles
    if any(k in path for k in ["component", "view", "page"]):
        return "frontend_ui"

    # framework hints
    if any(k in path for k in ["react", "vite"]):
        return "frontend"

    if any(k in path for k in ["express", "nestjs"]):
        return "backend_api"

    # fallback
    if "frontend" in path:
        return "frontend"

    if "backend" in path:
        return "backend"

    return "unknown"

def is_compatible_context(ctx1: str, ctx2: str) -> bool:

    # exact match → always OK
    if ctx1 == ctx2:
        return True

    # allow backend framework mixing
    backend_family = {
        "backend_api"
    }

    if ctx1 in backend_family and ctx2 in backend_family:
        return True

    # allow frontend grouping
    if ctx1.startswith("frontend") and ctx1 == ctx2:
        return True

    return False

def cluster_functions(functions, threshold=0.70):
    clusters = []
    used = set()

    for i, fn1 in enumerate(functions):
        if i in used:
            continue

        cluster = [fn1]
        used.add(i)

        for j in range(i + 1, len(functions)):
            if j in used:
                continue

            fn2 = functions[j]

            name_score = similarity(fn1.name, fn2.name)
            desc_score = similarity(fn1.description, fn2.description)

            score = 0.75 * name_score + 0.25 * desc_score

            ctx1 = get_context(fn1.file)
            ctx2 = get_context(fn2.file)

            if score > threshold and is_compatible_context(ctx1, ctx2):
                cluster.append(fn2)
                used.add(j)

        clusters.append(cluster)

    # Classification happens AFTER clustering
    safe_clusters = []
    ambiguous_clusters = []

    for cluster in clusters:
        if len(cluster) <= 1:
            continue

        if is_safe_duplicate(cluster):
            safe_clusters.append(cluster)
        else:
            ambiguous_clusters.append(cluster)

    return {
        "safe": safe_clusters,
        "ambiguous": ambiguous_clusters
    }