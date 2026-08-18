import re
from celery import Celery
from sqlalchemy import select
from app.config import get_settings
from app.database import SessionLocal
from app.models import Norm, ProcessingStatus, Provision, Relation
from app.services.extractor import extract_obligations
from app.services.graph import upsert_norm
from app.services.parser import segment_legal_text

settings = get_settings()
celery = Celery("regulagraph", broker=settings.redis_url, backend=settings.redis_url)
REFERENCE = re.compile(r"(?i)(altera|revoga|regulamenta|nos termos d[aeo])\s+(?:a|o)?\s*([^.;\n]{5,120})")


@celery.task(name="process_norm")
def process_norm(norm_id: str):
    with SessionLocal() as db:
        norm = db.scalar(select(Norm).where(Norm.id == norm_id))
        if not norm:
            return {"error": "not found"}
        norm.status = ProcessingStatus.processing
        db.commit()
        try:
            pages = [(1, norm.raw_text)]
            provisions = segment_legal_text(pages)
            graph_relations = []
            for item in provisions:
                obligations = extract_obligations(norm.id, item.label, item.page, item.text)
                db.add(Provision(norm_id=norm.id, label=item.label, text=item.text,
                                 page=item.page, position=item.position,
                                 extraction={"obligations": [o.model_dump() for o in obligations]}))
                for match in REFERENCE.finditer(item.text):
                    relation = {"type": match.group(1).upper(), "target": match.group(2).strip()}
                    graph_relations.append(relation)
                    db.add(Relation(source_norm_id=norm.id, target_reference=relation["target"],
                                    relation_type=relation["type"], evidence=match.group(0),
                                    page=item.page, confidence=0.8))
            norm.status = ProcessingStatus.completed
            db.commit()
            upsert_norm(norm, graph_relations)
            return {"provisions": len(provisions), "relations": len(graph_relations)}
        except Exception as exc:
            norm.status = ProcessingStatus.failed
            norm.metadata_json = {"error": str(exc)}
            db.commit()
            raise
