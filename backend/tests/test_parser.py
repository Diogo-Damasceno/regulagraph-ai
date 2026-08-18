from app.services.parser import segment_legal_text, sha256


def test_segments_articles_and_preserves_page():
    result = segment_legal_text([(3, "Art. 1º Deverá entregar.\nArt. 2º Fica revogado.")])
    assert [item.label for item in result] == ["Art. 1º", "Art. 2º"]
    assert all(item.page == 3 for item in result)


def test_hash_is_stable():
    assert sha256(b"norma") == sha256(b"norma")
