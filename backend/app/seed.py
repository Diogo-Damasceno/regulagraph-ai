from datetime import date
from app.database import Base, SessionLocal, engine
from app.models import Norm
from app.services.parser import sha256
from app.worker import process_norm

TEXT = """RESOLUÇÃO DEMONSTRATIVA Nº 1\nArt. 1º As distribuidoras deverão enviar relatório de conformidade em até 30 dias.\nArt. 2º Esta resolução entra em vigor na data de sua publicação."""

Base.metadata.create_all(bind=engine)
with SessionLocal() as db:
    digest = sha256(TEXT.encode())
    norm = Norm(title="Resolução demonstrativa nº 1", agency="ANEEL", number="1",
                file_hash=digest, raw_text=TEXT, effective_from=date.today())
    db.add(norm); db.commit(); db.refresh(norm)
    process_norm(norm.id)
    print(norm.id)
