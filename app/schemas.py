from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field


class RecipientInput(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    email: EmailStr
    course: str = Field(min_length=2, max_length=200)


class GenerationRequest(BaseModel):
    certificate_title: str = Field(
        default="Certificate of Completion",
        min_length=2,
        max_length=200,
    )
    event_name: str = Field(min_length=2, max_length=200)
    event_date: str = Field(min_length=2, max_length=100)
    recipients: List[RecipientInput] = Field(min_length=1)


class RecipientStatus(BaseModel):
    recipient_id: int
    name: str
    email: str
    status: str
    certificate_id: Optional[str] = None
    error_message: Optional[str] = None
    download_url: Optional[str] = None


class JobResponse(BaseModel):
    job_id: int
    status: str
    total: int
    completed: int
    failed: int
    progress_percent: float
    created_at: datetime
    updated_at: datetime
    recipients: List[RecipientStatus] = []
