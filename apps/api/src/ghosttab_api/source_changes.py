"""Compare active evidence with an already-authorized visible snapshot.

No provider/model calls or arbitrary version lookup. Dependencies identify claims
to review; they do not prove that a claim's meaning has changed.
"""


def source_changes(evidence, snapshot, citations):
    if not snapshot:
        return []
    previous = {item["id"]: item for item in citations}
    changes = []
    for current in evidence:
        before = previous.get(current["id"])
        if before and before["version_id"] == current["version_id"]:
            continue
        claims = []
        if before:
            for section, points in (
                ("summary", [snapshot.brief["summary"]]),
                ("fact", snapshot.brief["facts"]),
                ("next_step", snapshot.brief["next_steps"]),
            ):
                for point in points:
                    quotes = list(
                        dict.fromkeys(
                            ref["quote"]
                            for ref in point["citations"]
                            if ref["evidence_id"] == current["id"]
                        )
                    )
                    if quotes:
                        claims.append({"section": section, "text": point["text"], "quotes": quotes})
        changes.append(
            {
                "kind": "updated" if before else "added",
                "current": current,
                "previous": {**before, "origin": current["origin"]} if before else None,
                "changed_fields": [
                    field
                    for field in ("title", "content", "url")
                    if before is None or before[field] != current[field]
                ],
                "claims_to_review": claims,
            }
        )
    return changes
