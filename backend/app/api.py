import hashlib
import json
from datetime import date
from pathlib import Path
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.config import get_settings
from app.database import get_db
from app.models import Norm, Provision, Relation, Review
from app.schemas import NormCreate, QuestionRequest, ReviewCreate
from app.services.diff import compare_provisions
from app.services.parser import extract_pdf, sha256
from app.services.search import temporal_search
from app.worker import process_norm

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/norms")
def list_norms(db: Session = Depends(get_db)):
    norms = db.scalars(select(Norm).order_by(Norm.created_at.desc())).all()
    return [{"id": n.id, "title": n.title, "agency": n.agency, "status": n.status,
             "effective_from": n.effective_from} for n in norms]


@router.post("/norms/text", status_code=201)
def create_text_norm(payload: NormCreate, db: Session = Depends(get_db)):
    digest = hashlib.sha256(payload.text.encode()).hexdigest()
    existing = db.scalar(select(Norm).where(Norm.file_hash == digest))
    if existing:
        raise HTTPException(409, detail={"message": "Documento duplicado", "id": existing.id})
    norm = Norm(**payload.model_dump(), file_hash=digest)
    db.add(norm)
    db.commit()
    db.refresh(norm)
    process_norm.delay(norm.id)
    return {"id": norm.id, "status": norm.status}


@router.post("/norms/upload", status_code=201)
async def upload_norm(title: str = Form(...), agency: str = Form(...),
                      effective_from: date | None = Form(None), file: UploadFile = File(...),
                      db: Session = Depends(get_db)):
    data = await file.read()
    digest = sha256(data)
    existing = db.scalar(select(Norm).where(Norm.file_hash == digest))
    if existing:
        raise HTTPException(409, detail={"message": "Documento duplicado", "id": existing.id})
    upload_dir = Path(get_settings().upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    path = upload_dir / f"{digest}.pdf"
    path.write_bytes(data)
    raw_text, _ = extract_pdf(path)
    norm = Norm(title=title, agency=agency, effective_from=effective_from,
                file_hash=digest, raw_text=raw_text, metadata_json={"filename": file.filename})
    db.add(norm)
    db.commit()
    db.refresh(norm)
    process_norm.delay(norm.id)
    return {"id": norm.id, "status": norm.status}


@router.get("/norms/{norm_id}")
def get_norm(norm_id: str, db: Session = Depends(get_db)):
    norm = db.get(Norm, norm_id)
    if not norm:
        raise HTTPException(404, "Norma não encontrada")
    provisions = db.scalars(select(Provision).where(Provision.norm_id == norm_id)
                            .order_by(Provision.position)).all()
    relations = db.scalars(select(Relation).where(Relation.source_norm_id == norm_id)).all()
    return {"id": norm.id, "title": norm.title, "agency": norm.agency, "status": norm.status,
            "provisions": [{"id": p.id, "label": p.label, "text": p.text, "page": p.page,
                            "extraction": p.extraction} for p in provisions],
            "relations": [{"type": r.relation_type, "target": r.target_reference,
                           "page": r.page, "evidence": r.evidence} for r in relations]}


@router.get("/compare/{old_id}/{new_id}")
def compare(old_id: str, new_id: str, db: Session = Depends(get_db)):
    old = db.scalars(select(Provision).where(Provision.norm_id == old_id)).all()
    new = db.scalars(select(Provision).where(Provision.norm_id == new_id)).all()
    if not old or not new:
        raise HTTPException(404, "Uma das normas ainda não foi processada")
    return {"changes": [item.model_dump() for item in compare_provisions(old, new)]}


@router.post("/questions")
def ask(payload: QuestionRequest, db: Session = Depends(get_db)):
    results = temporal_search(db, payload.question, payload.reference_date, payload.agency)
    evidence = [{"document_id": n.id, "title": n.title, "provision": p.label,
                 "page": p.page, "quote": p.text[:500], "score": score}
                for score, n, p in results]
    answer = "Foram encontradas evidências relevantes." if evidence else "Não encontrei evidência suficiente."
    return {"answer": answer, "reference_date": payload.reference_date, "evidence": evidence,
            "requires_human_review": not bool(evidence)}


@router.post("/reviews", status_code=201)
def review(payload: ReviewCreate, db: Session = Depends(get_db)):
    item = Review(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": item.id}


@router.post("/evaluations/run")
def evaluate():
    path = Path(__file__).parents[1] / "evaluation" / "golden.jsonl"
    cases = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    correct = sum(case["expected_type"] == case["predicted_type"] for case in cases)
    citations = sum(bool(case.get("citation_valid")) for case in cases)
    total = len(cases) or 1
    return {"cases": len(cases), "accuracy": correct / total,
            "citation_accuracy": citations / total, "dataset": "golden.jsonl"}
