from pydantic import BaseModel


class PrintJobResponse(BaseModel):
    success: bool = True
    job_id: int
    printer: str
    filename: str
    status: str
