
from typing import Literal

from fastapi import (
    APIRouter,
    File,
    HTTPException,
    Query,
    UploadFile,
)
from pydantic import BaseModel, Field

from app.retrieval.retriever import search_evidence
from app.schemas.evidence import (
    CommitmentCreate,
    CommitmentResponse,
    DocumentResponse,
    SearchResponse,
)
from app.services.evidence_service import (
    MAX_DOCUMENT_SIZE,
    create_commitment,
    get_chunk,
    list_commitments,
    list_documents,
    require_case,
    update_commitment_status,
    upload_document,
)

router = APIRouter(
    prefix="/cases",
    tags=["Evidence & Commitments"],
)


class StatusUpdate(BaseModel):
    status: Literal[
        "open", "in_progress", "completed", "blocked"
    ]


class ChunkResponse(BaseModel):
    chunk_id: int
    document_id: int
    filename: str
    source_location: str
    content: str


@router.post(
    "/{case_id}/documents",
    response_model=DocumentResponse,
    status_code=201,
)
async def upload_evidence_document(
    case_id: int,
    file: UploadFile = File(...),
):
    try:
        content = await file.read(MAX_DOCUMENT_SIZE + 1)

        if len(content) > MAX_DOCUMENT_SIZE:
            raise HTTPException(
                status_code=413,
                detail="Document exceeds 5 MB",
            )

        return upload_document(
            case_id,
            file.filename or "",
            content,
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

    finally:
        await file.close()


@router.get(
    "/{case_id}/documents",
    response_model=list[DocumentResponse],
)
def get_documents(case_id: int):
    try:
        return list_documents(case_id)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc


@router.get(
    "/{case_id}/evidence/search",
    response_model=SearchResponse,
)
def search_case_evidence(
    case_id: int,
    q: str = Query(min_length=2, max_length=300),
    limit: int = Query(default=5, ge=1, le=20),
):
    try:
        require_case(case_id)
        results = search_evidence(case_id, q, limit)

        return SearchResponse(
            case_id=case_id,
            query=q,
            results=results,
        )
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc


@router.get(
    "/{case_id}/evidence/chunks/{chunk_id}",
    response_model=ChunkResponse,
)
def read_evidence_chunk(case_id: int, chunk_id: int):
    try:
        chunk = get_chunk(case_id, chunk_id)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc

    if chunk is None:
        raise HTTPException(
            status_code=404,
            detail="Evidence chunk not found",
        )

    return chunk


@router.post(
    "/{case_id}/commitments",
    response_model=CommitmentResponse,
    status_code=201,
)
def add_commitment(
    case_id: int,
    data: CommitmentCreate,
):
    try:
        return create_commitment(case_id, data)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get(
    "/{case_id}/commitments",
    response_model=list[CommitmentResponse],
)
def get_commitments(case_id: int):
    try:
        return list_commitments(case_id)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc


@router.patch(
    "/{case_id}/commitments/{commitment_id}",
    response_model=CommitmentResponse,
)
def change_commitment_status(
    case_id: int,
    commitment_id: int,
    data: StatusUpdate,
):
    try:
        return update_commitment_status(
            case_id, commitment_id, data.status
        )
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
