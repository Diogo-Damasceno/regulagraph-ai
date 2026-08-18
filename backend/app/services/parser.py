import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
import fitz


@dataclass
class ParsedProvision:
    label: str
    text: str
    page: int
    position: int


ARTICLE = re.compile(r"(?im)^(Art\.\s*\d+[ºo]?(?:,?\s*§\s*\d+[ºo]?)?)")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def extract_pdf(path: Path) -> tuple[str, list[tuple[int, str]]]:
    pages = []
    with fitz.open(path) as document:
        for number, page in enumerate(document, start=1):
            pages.append((number, page.get_text("text")))
    return "\n".join(text for _, text in pages), pages


def segment_legal_text(pages: list[tuple[int, str]]) -> list[ParsedProvision]:
    results: list[ParsedProvision] = []
    position = 0
    for page_number, text in pages:
        matches = list(ARTICLE.finditer(text))
        if not matches and text.strip():
            results.append(ParsedProvision(f"Página {page_number}", text.strip(), page_number, position))
            position += 1
            continue
        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            block = text[match.start():end].strip()
            results.append(ParsedProvision(match.group(1).strip(), block, page_number, position))
            position += 1
    return results
