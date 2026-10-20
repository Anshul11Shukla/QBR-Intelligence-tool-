
from app.services.qbr_context_service import build_qbr_context
from fastapi import APIRouter, HTTPException

from app.schemas.kpi import AnalysisResponse
from app.services.analytics_service import analyze_case
from app.agents.insight_agent import generate_qbr_insights
from app.agents.openai_agent import generate_ai_qbr_insights

router = APIRouter(
    prefix="/cases",
    tags=["KPI Analytics"],
)


@router.get(
    "/{case_id}/analytics",
    response_model=AnalysisResponse,
)
def get_case_analytics(case_id: int):
    try:
        return analyze_case(case_id)
    except LookupError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc


@router.get("/{case_id}/insights")
def get_case_insights(case_id: int):
    try:
        analysis = analyze_case(case_id)

        if hasattr(analysis, "model_dump"):
            analysis_data = analysis.model_dump()
        elif isinstance(analysis, dict):
            analysis_data = analysis
        else:
            raise ValueError("Unsupported analytics response format")

        return generate_qbr_insights(analysis_data)

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

@router.get("/{case_id}/ai-insights")
def get_case_ai_insights(case_id: int):
    try:
        analysis = analyze_case(case_id)

        if hasattr(analysis, "model_dump"):
            analysis = analysis.model_dump()

        return generate_ai_qbr_insights(analysis)

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

@router.get("/{case_id}/qbr-context")
def get_case_qbr_context(case_id: int):
    try:
        return build_qbr_context(case_id)

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
