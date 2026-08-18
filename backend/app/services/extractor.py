import json
import re
from openai import OpenAI
from app.config import get_settings
from app.schemas import Evidence, Obligation


MODAL = re.compile(r"(?i)(deverá|deve|fica obrigado|é obrigatório)\s+(.{5,220})")
SUBJECT = re.compile(r"(?i)(concessionárias?|distribuidoras?|agentes?|empresas?|operadores?)")
DEADLINE = re.compile(r"(?i)(?:prazo de|em até)\s+(\d+\s+(?:dias|meses|anos))")


def heuristic_obligations(document_id: str, label: str, page: int, text: str) -> list[Obligation]:
    modal = MODAL.search(text)
    if not modal:
        return []
    subject = SUBJECT.search(text)
    deadline = DEADLINE.search(text)
    return [Obligation(
        subject=subject.group(1) if subject else "entidade regulada não identificada",
        action=modal.group(2).split(".")[0].strip(),
        deadline=deadline.group(1) if deadline else None,
        confidence=0.65,
        evidence=Evidence(document_id=document_id, provision=label, page=page, quote=modal.group(0)[:300]),
    )]


def extract_obligations(document_id: str, label: str, page: int, text: str) -> list[Obligation]:
    settings = get_settings()
    if settings.llm_provider != "openai" or not settings.openai_api_key:
        return heuristic_obligations(document_id, label, page, text)
    client = OpenAI(api_key=settings.openai_api_key)
    response = client.responses.create(
        model=settings.openai_model,
        input=[{"role": "system", "content": "Extraia obrigações jurídicas. Não invente dados."},
               {"role": "user", "content": text}],
        text={"format": {"type": "json_schema", "name": "obligations", "schema": {
            "type": "object", "properties": {"items": {"type": "array", "items": {
                "type": "object", "properties": {"subject": {"type": "string"},
                "action": {"type": "string"}, "deadline": {"type": ["string", "null"]},
                "confidence": {"type": "number"}},
                "required": ["subject", "action", "deadline", "confidence"],
                "additionalProperties": False}}}, "required": ["items"], "additionalProperties": False}, "strict": True}},
    )
    data = json.loads(response.output_text)
    return [Obligation(**item, evidence=Evidence(
        document_id=document_id, provision=label, page=page, quote=text[:300]
    )) for item in data["items"]]
