from difflib import SequenceMatcher
from app.schemas import Change


def compare_provisions(old_items, new_items) -> list[Change]:
    old = {item.label: item.text for item in old_items}
    new = {item.label: item.text for item in new_items}
    changes: list[Change] = []
    for label in sorted(old.keys() | new.keys()):
        before, after = old.get(label), new.get(label)
        if before == after:
            continue
        if before is None:
            kind, confidence = "added", 1.0
        elif after is None:
            kind, confidence = "revoked", 1.0
        else:
            kind = "modified"
            confidence = round(1 - SequenceMatcher(None, before, after).ratio(), 3)
        changes.append(Change(
            change_type=kind, provision=label, before=before, after=after,
            summary=f"Dispositivo {kind}", confidence=max(confidence, 0.01),
        ))
    return changes
