
import sqlite3

from app.database import get_connection
from app.schemas.case import CaseCreate


class DuplicateCaseError(Exception):
    pass


def create_case(data: CaseCreate):
    try:
        with get_connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO qbr_cases (customer_name, quarter, year)
                VALUES (?, ?, ?)
                """,
                (data.customer_name, data.quarter, data.year),
            )
            case_id = cursor.lastrowid
            connection.commit()
    except sqlite3.IntegrityError as exc:
        raise DuplicateCaseError(
            "A workspace already exists for this customer and quarter"
        ) from exc

    return get_case(case_id)


def get_case(case_id: int):
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM qbr_cases WHERE id = ?",
            (case_id,),
        ).fetchone()

    return dict(row) if row else None


def list_cases():
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM qbr_cases ORDER BY created_at DESC, id DESC"
        ).fetchall()

    return [dict(row) for row in rows]
