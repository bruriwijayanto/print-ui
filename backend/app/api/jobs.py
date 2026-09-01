from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_job_service
from app.schemas.job import JobCancelResponse, JobDetail, JobSummary
from app.services.cups import CupsConnectionError, CupsOperationError, JobNotFoundError
from app.services.job_service import JobNotCancelableError, JobService

router = APIRouter(tags=["jobs"])


@router.get("/jobs", response_model=list[JobSummary])
def list_jobs(job_service: JobService = Depends(get_job_service)):
    try:
        return job_service.list_jobs()
    except CupsConnectionError as exc:
        raise HTTPException(status_code=503, detail={"code": "CUPS_UNAVAILABLE", "message": str(exc)}) from exc
    except CupsOperationError as exc:
        raise HTTPException(status_code=502, detail={"code": "CUPS_ERROR", "message": str(exc)}) from exc


@router.get("/jobs/{job_id}", response_model=JobDetail)
def get_job(job_id: int, job_service: JobService = Depends(get_job_service)):
    try:
        return job_service.get_job(job_id)
    except JobNotFoundError as exc:
        raise HTTPException(status_code=404, detail={"code": "JOB_NOT_FOUND", "message": str(exc)}) from exc
    except CupsConnectionError as exc:
        raise HTTPException(status_code=503, detail={"code": "CUPS_UNAVAILABLE", "message": str(exc)}) from exc
    except CupsOperationError as exc:
        raise HTTPException(status_code=502, detail={"code": "CUPS_ERROR", "message": str(exc)}) from exc


@router.delete("/jobs/{job_id}", response_model=JobCancelResponse)
def cancel_job(job_id: int, job_service: JobService = Depends(get_job_service)):
    try:
        job_service.cancel_job(job_id)
        return {"success": True, "job_id": job_id, "status": "canceled"}
    except JobNotFoundError as exc:
        raise HTTPException(status_code=404, detail={"code": "JOB_NOT_FOUND", "message": str(exc)}) from exc
    except JobNotCancelableError as exc:
        raise HTTPException(status_code=409, detail={"code": "JOB_NOT_CANCELABLE", "message": str(exc)}) from exc
    except CupsConnectionError as exc:
        raise HTTPException(status_code=503, detail={"code": "CUPS_UNAVAILABLE", "message": str(exc)}) from exc
    except CupsOperationError as exc:
        raise HTTPException(status_code=502, detail={"code": "CUPS_ERROR", "message": str(exc)}) from exc
