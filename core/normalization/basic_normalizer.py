# core/normalization/basic_normalizer.py

import re

def to_snake_case(name: str) -> str:
    name = name.replace("-", "_").replace(" ", "_")

    # camelCase → snake_case
    name = re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()

    return name


def normalize_variable(var: str) -> str:
    if not var or "." not in var:
        return var

    entity, name = var.split(".", 1)

    entity = entity.lower().strip()
    name = name.strip()

    # Convert camelCase → snake_case
    name = to_snake_case(name)

    # Remove entity prefix duplication
    if name.startswith(entity + "_"):
        name = name[len(entity) + 1:]

    # Normalize common suffixes
    name = _normalize_suffix(name)

    return f"{entity}.{name}"


def _normalize_suffix(name: str) -> str:
    """
    Generic suffix normalization (SAFE version)
    """

    # remove prefixes like new_, old_, temp_
    name = re.sub(r"^(new|old|temp|updated)_", "", name)

    # unify id patterns safely
    if name.endswith("_id"):
        return "id"

    # unify list patterns
    if name.endswith("_list") or name.endswith("_array"):
        return "list"

    # DO NOT collapse semantic words
    # keep them as-is:
    # details, data, info, success, status, result

    return name


def normalize_function_name(name: str) -> str:
    return to_snake_case(name)