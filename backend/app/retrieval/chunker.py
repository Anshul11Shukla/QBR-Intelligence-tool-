
from dataclasses import dataclass

from app.retrieval.document_parser import ParsedSection


@dataclass
class TextChunk:
    location: str
    text: str


def chunk_sections(
    sections: list[ParsedSection],
    max_chars: int = 900,
    overlap: int = 120,
) -> list[TextChunk]:
    if max_chars <= 0 or overlap < 0 or overlap >= max_chars:
        raise ValueError("Invalid chunk configuration")

    chunks = []

    for section in sections:
        text = " ".join(section.text.split())

        if not text:
            continue

        start = 0

        while start < len(text):
            end = min(start + max_chars, len(text))

            if end < len(text):
                split = text.rfind(" ", start, end)

                if split > start + max_chars // 2:
                    end = split

            chunk_text = text[start:end].strip()

            if chunk_text:
                chunks.append(
                    TextChunk(
                        location=section.location,
                        text=chunk_text,
                    )
                )

            if end >= len(text):
                break

            start = max(start + 1, end - overlap)

    return chunks
