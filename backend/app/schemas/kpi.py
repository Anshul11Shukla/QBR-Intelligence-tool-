
from typing import Literal
from pydantic import BaseModel

Direction = Literal["higher", "lower"]
Period = Literal["previous", "current"]


class KPIRecord(BaseModel):
    metric: str
    value: float | None
    unit: str
    direction: Direction
    target: float | None = None
    source_sheet: str
    source_row: int


class KPIResult(BaseModel):
    metric: str
    unit: str
    direction: Direction
    previous_value: float | None
    current_value: float | None
    target: float | None
    absolute_change: float | None
    percentage_change: float | None
    target_met: bool | None
    status: str
    alerts: list[str]
    sources: dict[str, str]


class AnalysisResponse(BaseModel):
    case_id: int
    metrics: list[KPIResult]
    summary: dict[str, int]
    warnings: list[str]
