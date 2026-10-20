from app.agents.qa_coach_agent import generate_customer_questions
from app.services.qa_coaching_service import enhance_qa_questions
from io import BytesIO
import re

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.database import get_connection
from app.services.qbr_context_service import build_qbr_context
from app.services.pptx_service import generate_qbr_pptx

router = APIRouter(
    prefix="/cases",
    tags=["QBR PowerPoint Export"],
)


def get_case_details(case_id: int) -> dict:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, customer_name, quarter, year
            FROM qbr_cases
            WHERE id = ?
            """,
            (case_id,),
        ).fetchone()

    if row is None:
        raise LookupError("QBR workspace not found")

    return dict(row)


@router.get("/{case_id}/export/pptx")
def export_qbr_powerpoint(case_id: int):
    try:
        case = get_case_details(case_id)

        context = build_qbr_context(case_id)
        questions = generate_customer_questions(context)
        questions = enhance_qa_questions(questions)

        context["questions"] = questions

        presentation_bytes = generate_qbr_pptx(
            context=context,
            customer_name=case["customer_name"],
            period=f"{case['quarter']} {case['year']}",
        )

        safe_customer = re.sub(
            r"[^A-Za-z0-9_-]+",
            "_",
            case["customer_name"],
        ).strip("_") or "Customer"

        filename = (
            f"QBR_{safe_customer}_"
            f"{case['quarter']}_{case['year']}.pptx"
        )

        return StreamingResponse(
            BytesIO(presentation_bytes),
            media_type=(
                "application/vnd.openxmlformats-officedocument."
                "presentationml.presentation"
            ),
            headers={
                "Content-Disposition": (
                    f'attachment; filename="{filename}"'
                ),
                "Cache-Control": "no-store",
            },
        )

    except LookupError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
