from dataclasses import dataclass
from app.services.diff import compare_provisions


@dataclass
class Item:
    label: str
    text: str


def test_detects_added_modified_and_revoked():
    old = [Item("Art. 1º", "Prazo de 30 dias"), Item("Art. 2º", "Antigo")]
    new = [Item("Art. 1º", "Prazo de 15 dias"), Item("Art. 3º", "Novo")]
    types = {item.change_type for item in compare_provisions(old, new)}
    assert types == {"added", "modified", "revoked"}
