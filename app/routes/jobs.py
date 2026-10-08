from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import GenerationJob, Recipient
from app.schemas import GenerationRequest, JobResponse, RecipientStatus
from app.services.job_processor import process_job

router = APIRouter(prefix="/jobs", tags=["Jobs"])


def build_job_response(job: GenerationJob) -> JobResponse:
    processed = job.completed + job.failed
    progress = (processed / job.total * 100) if job.total else 0.0

    recipients = []
    for recipient in job.recipients:
        download_url = None
        if recipient.status == "completed":
            download_url = f"/api/certificates/{recipient.id}/download"

        recipients.append(
            RecipientStatus(
                recipient_id=recipient.id,
                name=recipient.name,
                email=recipient.email,
                status=recipient.status,
                certificate_id=recipient.certificate_id,
                error_message=recipient.error_message,
                download_url=download_url,
            )
        )

    return JobResponse(
        job_id=job.id,
        status=job.status,
        total=job.total,
        completed=job.completed,
        failed=job.failed,
        progress_percent=round(progress, 2),
        created_at=job.created_at,
        updated_at=job.updated_at,
        recipients=recipients,
    )


@router.post("", response_model=JobResponse, status_code=202)
def create_generation_job(
    request: GenerationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    job = GenerationJob(
        status="queued",
        total=len(request.recipients),
    )
    db.add(job)
    db.flush()

    for item in request.recipients:
        recipient = Recipient(
            job_id=job.id,
            name=item.name.strip(),
            email=str(item.email),
            course=item.course.strip(),
            status="pending",
        )
        db.add(recipient)

    db.commit()
    db.refresh(job)

    background_tasks.add_task(
        process_job,
        job.id,
        request.event_name,
        request.event_date,
        request.certificate_title,
    )

    return build_job_response(job)


@router.get("/{job_id}", response_model=JobResponse)
def get_job_status(
    job_id: int,
    db: Session = Depends(get_db),
):
    job = db.query(GenerationJob).filter(
        GenerationJob.id == job_id
    ).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return build_job_response(job)
