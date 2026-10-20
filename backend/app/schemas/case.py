
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class CaseCreate(BaseModel):
    customer_name: str = Field(min_length=2, max_length=150)
    quarter: str
    year: int = Field(ge=2020, le=2100)

    @field_validator("customer_name")
    @classmethod
    def validate_customer_name(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise ValueError("Customer name must contain at least 2 characters")
        return value

    @field_validator("quarter")
    @classmethod
    def validate_quarter(cls, value: str) -> str:
        value = value.upper().strip()
        if value not in {"Q1", "Q2", "Q3", "Q4"}:
            raise ValueError("Quarter must be Q1, Q2, Q3, or Q4")
        return value


class CaseResponse(BaseModel):
    id: int
    customer_name: str
    quarter: str
    year: int
    created_at: datetime
