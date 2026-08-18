import re
from datetime import date
from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from app.models import Norm, Provision, ProcessingStatus


def temporal_search(db: Session, question: str, reference_date: date | None, agency: str | None):
    terms = [term.lower() for term in re.findall(r"\w{4,}", question)][:12]
    query = select(Norm).where(Norm.status == ProcessingStatus.completed)
    if agency:
        query = query.where(Norm.agency == agency)
    if reference_date:
        query = query.where(or_(Norm.effective_from.is_(None), Norm.effective_from <= reference_date))
        query = query.where(or_(Norm.effective_to.is_(None), Norm.effective_to >= reference_date))
    norms = db.scalars(query).all()
    candidates = []
    for norm in norms:
        for provision in db.scalars(select(Provision).where(Provision.norm_id == norm.id)):
            score = sum(term in provision.text.lower() for term in terms)
            if score:
                candidates.append((score, norm, provision))
    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[:5]
