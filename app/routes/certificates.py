from pathlib import Path
from tempfile import NamedTemporaryFile
from zipfile import ZIP_DEFLATED, ZipFile

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import GenerationJob, Recipient

router = APIRouter(prefix="/certificates", tags=["Certificates"])


@router.get("/{recipient_id}/download")
def download_certificate(
    recipient_id: int,
    db: Session = Depends(get_db),
):
    recipient = db.query(Recipient).filter(
        Recipient.id == recipient_id
    ).first()

    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")

    if recipient.status != "completed" or not recipient.file_path:
        raise HTTPException(
            status_code=409,
            detail="Certificate is not available yet",
        )

    file_path = Path(recipient.file_path)

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Certificate file not found",
        )

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=file_path.name,
    )


@router.get("/job/{job_id}/download-all")
def download_all_certificates(
    job_id: int,
    db: Session = Depends(get_db),
):
    job = db.query(GenerationJob).filter(
        GenerationJob.id == job_id
    ).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    completed = [
        r for r in job.recipients
        if r.status == "completed" and r.file_path
    ]

    if not completed:
        raise HTTPException(
            status_code=409,
            detail="No generated certificates are available",
        )

    temp = NamedTemporaryFile(
        delete=False,
        suffix=".zip",
        prefix=f"job_{job_id}_",
    )
    zip_path = temp.name
    temp.close()

    with ZipFile(zip_path, "w", ZIP_DEFLATED) as archive:
        for recipient in completed:
            path = Path(recipient.file_path)
            if path.exists():
                archive.write(path, arcname=path.name)

    return FileResponse(
        path=zip_path,
        media_type="application/zip",
        filename=f"job_{job_id}_certificates.zip",
    )
