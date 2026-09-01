from typing import Optional

from pydantic import BaseModel


class PrinterCapabilities(BaseModel):
    media: list[str] = []
    color: bool = False
    duplex: bool = False
    resolution: list[str] = []
    copies_supported: bool = False
    max_copies: Optional[int] = None
    page_ranges_supported: bool = False
    orientation_supported: bool = False


class PrinterSummary(BaseModel):
    name: str
    description: str
    state: str
    state_message: str
    accepting_jobs: bool
    shared: bool
    device_uri: Optional[str] = None
    current_job: Optional[int] = None
    queue_count: int = 0


class PrinterDetail(PrinterSummary):
    location: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    capabilities: PrinterCapabilities
