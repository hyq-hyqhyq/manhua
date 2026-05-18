def create_entity_pool(entities: list[dict[str, str]]) -> dict:
    return {
        entity["entity_id"]: {
            "description": entity["description"],
            "refs": [],
        }
        for entity in entities
    }


def next_ref_id(entity_pool: dict, entity_id: str) -> str:
    if entity_id not in entity_pool:
        raise ValueError(f"Unknown entity_id: {entity_id}")
    return f"{entity_id}_ref_{len(entity_pool[entity_id]['refs']):03d}"


def append_ref(
    entity_pool: dict,
    entity_id: str,
    rgba_path: str,
    source: str,
    note: str,
) -> dict:
    ref = {
        "ref_id": next_ref_id(entity_pool, entity_id),
        "rgba_path": rgba_path,
        "source": source,
        "note": note,
    }
    entity_pool[entity_id]["refs"].append(ref)
    return ref
