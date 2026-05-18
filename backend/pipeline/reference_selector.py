def select_references(entity_pool: dict, entities_used: list[str]) -> dict[str, list[dict]]:
    selected: dict[str, list[dict]] = {}

    for entity_id in entities_used:
        refs = entity_pool.get(entity_id, {}).get("refs", [])
        if len(refs) <= 3:
            selected[entity_id] = refs[:]
            continue

        anchor_refs = [ref for ref in refs if ref.get("source") == "anchor"]
        recent_refs = [ref for ref in refs if ref.get("source") != "anchor"][-2:]
        chosen = anchor_refs[:1] + recent_refs
        selected[entity_id] = chosen[:3]

    return selected
