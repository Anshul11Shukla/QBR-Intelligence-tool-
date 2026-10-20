
from fastapi import (
    APIRouter,
    File,
    HTTPException,
    UploadFile,
)

from app.services.file_service import (
    MAX_FILE_SIZE,
    save_kpi_upload,
)

router = APIRouter(
    prefix="/cases",
    tags=["KPI Uploads"],
)


@router.post("/{case_id}/upload")
async def upload_kpi_file(
    case_id: int,
    period: str,
    file: UploadFile = File(...),
):
    if period not in {"previous", "current"}:
        raise HTTPException(
            status_code=422,
            detail="Period must be previous or current",
        )

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required",
        )

    try:
        content = await file.read(MAX_FILE_SIZE + 1)

        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="File exceeds 5 MB",
            )

        return save_kpi_upload(
            case_id,
            period,
            file.filename,
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
