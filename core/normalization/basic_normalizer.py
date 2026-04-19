# core/normalization/basic_normalizer.py

import re


def to_snake_case(name: str) -> str:
    name = name.replace("-", "_").replace(" ", "_")

    # camelCase → snake_case
    name = re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()

    return name


def normalize_variable(var: str) -> str:
    """
    Input: userId OR user.userId OR user_id
    Output: user.id
    """

    if "." in var:
        entity, attr = var.split(".", 1)
    else:
        entity, attr = "unknown", var

    entity = to_snake_case(entity)
    attr = to_snake_case(attr)

    # common canonicalizations
    if attr in ["userid", "user_id", "user_id_"]:
        attr = "id"

    if attr in ["usernameoremail", "username_or_email"]:
        attr = "username_or_email"

    return f"{entity}.{attr}"


def normalize_function_name(name: str) -> str:
    return to_snake_case(name)