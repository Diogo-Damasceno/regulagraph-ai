from app.services.extractor import heuristic_obligations


def test_extracts_obligation_with_deadline():
    items = heuristic_obligations("doc", "Art. 1º", 2,
        "As distribuidoras deverão enviar relatório em até 15 dias.")
    assert len(items) == 1
    assert items[0].deadline == "15 dias"
    assert items[0].evidence.page == 2
