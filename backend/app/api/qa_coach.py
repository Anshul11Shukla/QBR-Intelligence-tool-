from app.services.qa_coaching_service import (
    enhance_qa_questions,
)
from fastapi import APIRouter, HTTPException

from app.agents.qa_coach_agent import (
    generate_customer_questions,
)
from app.services.qbr_context_service import (
    build_qbr_context,
)


router = APIRouter(
    prefix="/cases",
    tags=["Customer Q&A Coach"],
)


@router.get("/{case_id}/qa-coach")
def get_customer_qa_coach(case_id: int):
    try:
        context = build_qbr_context(case_id)

        questions = generate_customer_questions(
            context
        )
        questions = enhance_qa_questions(questions)

        return {
            "case_id": case_id,
            "total_questions": len(questions),
            "questions": questions,
            "generation_mode": "deterministic_qa",
        }

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
