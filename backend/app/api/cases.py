
from fastapi import APIRouter, HTTPException, status

from app.schemas.case import CaseCreate, CaseResponse
from app.services.case_service import (
    DuplicateCaseError,
    create_case,
    get_case,
    list_cases,
)

router = APIRouter(prefix="/cases", tags=["QBR Cases"])


@router.post(
    "",
    response_model=CaseResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_qbr_case(data: CaseCreate):
    try:
        return create_case(data)
    except DuplicateCaseError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc


@router.get("", response_model=list[CaseResponse])
def get_all_qbr_cases():
    return list_cases()


@router.get("/{case_id}", response_model=CaseResponse)
def get_qbr_case(case_id: int):
    case = get_case(case_id)

    if case is None:
        raise HTTPException(
            status_code=404,
            detail="QBR workspace not found",
        )

    return case
