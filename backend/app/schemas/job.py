from typing import Optional

from pydantic import BaseModel


class JobSummary(BaseModel):
    job_id: int
    printer: str
    document: str
    user: str
    submitted_at: Optional[str] = None
    status: str


class JobDetail(JobSummary):
    owner: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    options: dict[str, str] = {}
    error: Optional[str] = None


class JobCancelResponse(BaseModel):
    success: bool = True
    job_id: int
    status: str = "canceled"
