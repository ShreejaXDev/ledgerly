from enum import Enum

from pydantic import BaseModel, Field


class ExportFormat(str, Enum):
    csv = "csv"
    xlsx = "xlsx"
    pdf = "pdf"


class ExportRequest(BaseModel):
    telegram_id: str
    username: str | None = None
    first_name: str
    last_name: str | None = None
    export_format: ExportFormat


class ExportResponse(BaseModel):
    file_path: str
    filename: str
    message: str = Field(default="Export generated successfully.")
