from uuid import uuid4
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import GenerationJob, Recipient
from app.services.certificate_generator import generate_certificate


def process_job(
    job_id: int,
    event_name: str,
    event_date: str,
    certificate_title: str,
):
    db: Session = SessionLocal()

    try:
        job = db.query(GenerationJob).filter(
            GenerationJob.id == job_id
        ).first()

        if not job:
            return

        job.status = "processing"
        db.commit()

        recipients = db.query(Recipient).filter(
            Recipient.job_id == job_id
        ).all()

        for recipient in recipients:
            try:
                recipient.status = "processing"
                db.commit()

                # This check makes invalid data safe even if the API
                # receives a malformed payload from another client.
                if not recipient.name.strip():
                    raise ValueError("Recipient name cannot be empty")

                certificate_id = f"CERT-{job_id}-{uuid4().hex[:10].upper()}"

                file_path = generate_certificate(
                    name=recipient.name,
                    course=recipient.course,
                    event_name=event_name,
                    event_date=event_date,
                    certificate_title=certificate_title,
                    certificate_id=certificate_id,
                )

                recipient.certificate_id = certificate_id
                recipient.file_path = file_path
                recipient.status = "completed"
                recipient.error_message = None
                job.completed += 1

            except Exception as exc:
                recipient.status = "failed"
                recipient.error_message = str(exc)
                job.failed += 1

            db.commit()

        job.status = "completed"
        db.commit()

    except Exception as exc:
        job.status = "failed"
        db.commit()
    finally:
        db.close()
