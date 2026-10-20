
import json

from app.analytics.ingestion import parse_workbook
from app.database import get_connection

MAX_FILE_SIZE = 5 * 1024 * 1024


def save_kpi_upload(
    case_id: int,
    period: str,
    filename: str,
    content: bytes,
):
    if period not in {"previous", "current"}:
        raise ValueError("Invalid reporting period")

    if not filename.lower().endswith(".xlsx"):
        raise ValueError("Only .xlsx files are supported")

    if not content:
        raise ValueError("The uploaded file is empty")

    if len(content) > MAX_FILE_SIZE:
        raise ValueError("File exceeds the 5 MB limit")

    records = parse_workbook(content)

    payload = json.dumps([
        record.model_dump() for record in records
    ])

    with get_connection() as connection:
        case = connection.execute(
            "SELECT id FROM qbr_cases WHERE id = ?",
            (case_id,),
        ).fetchone()

        if case is None:
            raise LookupError("QBR workspace not found")

        connection.execute(
            """
            INSERT INTO kpi_snapshots (
                case_id, period, filename, records_json
            )
            VALUES (?, ?, ?, ?)
            ON CONFLICT(case_id, period)
            DO UPDATE SET
                filename = excluded.filename,
                records_json = excluded.records_json,
                uploaded_at = CURRENT_TIMESTAMP
            """,
            (case_id, period, filename, payload),
        )

        connection.commit()

    return {
        "case_id": case_id,
        "period": period,
        "filename": filename,
        "records_imported": len(records),
    }


def get_kpi_snapshots(case_id: int):
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT period, filename, records_json
            FROM kpi_snapshots
            WHERE case_id = ?
            """,
            (case_id,),
        ).fetchall()

    return {
        row["period"]: {
            "filename": row["filename"],
            "records": json.loads(row["records_json"]),
        }
        for row in rows
    }
