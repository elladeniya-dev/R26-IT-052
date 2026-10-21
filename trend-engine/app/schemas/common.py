from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PageMeta(BaseModel):
    page: int
    size: int
    total: int


class Page(BaseModel, Generic[T]):
    data: list[T]
    meta: PageMeta


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


class HealthResponse(BaseModel):
    status: str


class ReadinessResponse(BaseModel):
    status: str
    database: bool
    model_loaded: bool
    model_name: str | None = None
    latest_snapshot_date: str | None = None
    is_stale: bool = False
