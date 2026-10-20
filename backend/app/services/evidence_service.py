
from pathlib import Path

from app.database import get_connection
from app.retrieval.chunker import chunk_sections
from app.retrieval.document_parser import (
    SUPPORTED_EXTENSIONS,
    parse_document,
)
from app.schemas.evidence import CommitmentCreate

MAX_DOCUMENT_SIZE = 5 * 1024 * 1024


def require_case(case_id: int):
    with get_connection() as connection:
        row = connection.execute(
            "SELECT id FROM qbr_cases WHERE id = ?",
            (case_id,),
        ).fetchone()

    if row is None:
        raise LookupError("QBR workspace not found")


def upload_document(
    case_id: int,
    filename: str,
    content: bytes,
):
    require_case(case_id)

    if not filename:
        raise ValueError("Filename is required")

    extension = Path(filename).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError("Unsupported document format")

    if not content or len(content) > MAX_DOCUMENT_SIZE:
        raise ValueError(
            "Document must be between 1 byte and 5 MB"
        )

    sections = parse_document(filename, content)
    chunks = chunk_sections(sections)

    if not chunks:
        raise ValueError("No searchable text found")

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO evidence_documents (
                case_id, filename, document_type, chunk_count
            )
            VALUES (?, ?, ?, ?)
            """,
            (case_id, filename, extension, len(chunks)),
        )

        document_id = cursor.lastrowid

        connection.executemany(
            """
            INSERT INTO evidence_chunks (
                document_id, source_location, content
            )
            VALUES (?, ?, ?)
            """,
            [
                (document_id, chunk.location, chunk.text)
                for chunk in chunks
            ],
        )

        connection.commit()

    return get_document(case_id, document_id)


def get_document(case_id: int, document_id: int):
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT * FROM evidence_documents
            WHERE id = ? AND case_id = ?
            """,
            (document_id, case_id),
        ).fetchone()

    return dict(row) if row else None


def list_documents(case_id: int):
    require_case(case_id)

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT * FROM evidence_documents
            WHERE case_id = ?
            ORDER BY id DESC
            """,
            (case_id,),
        ).fetchall()

    return [dict(row) for row in rows]


def get_chunk(case_id: int, chunk_id: int):
    require_case(case_id)

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                c.id AS chunk_id,
                c.document_id,
                c.source_location,
                c.content,
                d.filename
            FROM evidence_chunks c
            JOIN evidence_documents d
                ON d.id = c.document_id
            WHERE c.id = ? AND d.case_id = ?
            """,
            (chunk_id, case_id),
        ).fetchone()

    return dict(row) if row else None


def create_commitment(
    case_id: int,
    data: CommitmentCreate,
):
    require_case(case_id)

    if data.source_document_id is not None:
        document = get_document(
            case_id, data.source_document_id
        )

        if document is None:
            raise ValueError(
                "Source document does not belong to this workspace"
            )

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO commitments (
                case_id, title, owner, due_date, status,
                source_document_id, source_location
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                case_id,
                data.title,
                data.owner,
                data.due_date.isoformat()
                    if data.due_date else None,
                data.status,
                data.source_document_id,
                data.source_location,
            ),
        )

        commitment_id = cursor.lastrowid
        connection.commit()

        row = connection.execute(
            "SELECT * FROM commitments WHERE id = ?",
            (commitment_id,),
        ).fetchone()

    return dict(row)


def list_commitments(case_id: int):
    require_case(case_id)

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT * FROM commitments
            WHERE case_id = ?
            ORDER BY
                CASE WHEN due_date IS NULL THEN 1 ELSE 0 END,
                due_date ASC,
                id DESC
            """,
            (case_id,),
        ).fetchall()

    return [dict(row) for row in rows]


def update_commitment_status(
    case_id: int,
    commitment_id: int,
    status: str,
):
    require_case(case_id)

    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE commitments
            SET status = ?
            WHERE id = ? AND case_id = ?
            """,
            (status, commitment_id, case_id),
        )

        if cursor.rowcount == 0:
            raise LookupError("Commitment not found")

        connection.commit()

        row = connection.execute(
            """
            SELECT * FROM commitments
            WHERE id = ? AND case_id = ?
            """,
            (commitment_id, case_id),
        ).fetchone()

    return dict(row)
