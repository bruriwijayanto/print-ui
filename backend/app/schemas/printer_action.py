from pydantic import BaseModel


class PrinterActionResponse(BaseModel):
    success: bool = True
    printer: str
    action: str
