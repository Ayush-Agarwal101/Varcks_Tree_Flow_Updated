# core/normalization/entity_normalizer.py

# CANONICAL ENTITY MAP

ENTITY_CANONICAL_MAP = {
    # user domain
    "user": "user",
    "users": "user",
    "customer": "user",
    "client": "user",
    "account": "user",
    "userid": "id",
    "user_id": "id",
    "userId": "id",
    "usernameOrEmail": "username_or_email",

    # order domain
    "order": "order",
    "orders": "order",

    # product domain
    "product": "product",
    "products": "product",
    "item": "product",

    # session/auth domain
    "session": "session",
    "token": "session",
    "jwt": "session",

    # cart
    "cart": "cart",

    # category
    "category": "category",
}

# ENTITY INFERENCE

def infer_entity_from_name(name: str) -> str:
    if not name:
        return "unknown"

    name = name.lower()

    if "user" in name:
        return "user"
    if "order" in name:
        return "order"
    if "product" in name:
        return "product"
    if "cart" in name:
        return "cart"
    if "token" in name or "session" in name:
        return "session"
    if "category" in name:
        return "category"

    return "unknown"

# NORMALIZATION FUNCTION

def normalize_entity(entity: str | None, fallback_name: str = "") -> str:
    """
    Normalize entity using:
    1. Canonical map
    2. Inference
    3. Fallback
    """

    # CASE 1 — Empty → infer
    if not entity or str(entity).strip() == "":
        return infer_entity_from_name(fallback_name)

    entity = entity.strip().lower()

    # CASE 2 — Canonical mapping
    if entity in ENTITY_CANONICAL_MAP:
        return ENTITY_CANONICAL_MAP[entity]

    # CASE 3 — Try inference from name
    inferred = infer_entity_from_name(fallback_name)
    if inferred != "unknown":
        return inferred

    # CASE 4 — keep as-is (new domain entity)
    return entity