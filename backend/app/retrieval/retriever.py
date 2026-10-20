
import re

from app.database import get_connection
from app.retrieval.citations import (
    build_citation,
    build_excerpt,
)
from app.schemas.evidence import EvidenceHit


def search_evidence(
    case_id: int,
    query: str,
    limit: int = 5,
) -> list[EvidenceHit]:
    words = re.findall(r"\w+", query.lower(), re.UNICODE)

    if not words:
        return []

    # Quote tokens so user text is not interpreted
    # as an FTS query expression.
    search_expression = " OR ".join(
        f'"{word}"' for word in words[:12]
    )

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                c.id AS chunk_id,
                d.id AS document_id,
                d.filename,
                c.source_location,
                c.content,
                bm25(evidence_fts) AS rank
            FROM evidence_fts
            JOIN evidence_chunks c
                ON c.id = evidence_fts.rowid
            JOIN evidence_documents d
                ON d.id = c.document_id
            WHERE evidence_fts MATCH ?
              AND d.case_id = ?
            ORDER BY rank ASC
            LIMIT ?
            """,
            (search_expression, case_id, limit),
        ).fetchall()

    results = []

    for row in rows:
        results.append(
            EvidenceHit(
                chunk_id=row["chunk_id"],
                document_id=row["document_id"],
                filename=row["filename"],
                source_location=row["source_location"],
                excerpt=build_excerpt(row["content"]),
                citation=build_citation(
                    row["document_id"],
                    row["filename"],
                    row["source_location"],
                    row["chunk_id"],
                ),
                relevance_score=round(
                    float(-row["rank"]), 4
                ),
            )
        )

    return results
