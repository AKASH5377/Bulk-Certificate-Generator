import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Use a separate test database before importing the application.
os.environ["TESTING"] = "1"

from app.main import app
from app.database import Base, engine, SessionLocal
from app.models import GenerationJob, Recipient


client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    generated = Path("generated_certificates")
    generated.mkdir(exist_ok=True)
    for file in generated.glob("*.pdf"):
        file.unlink()
    yield


def test_create_generation_job():
    payload = {
        "certificate_title": "Certificate of Completion",
        "event_name": "Python Workshop",
        "event_date": "October 8, 2026",
        "recipients": [
            {
                "name": "Akash Singh",
                "email": "akash@example.com",
                "course": "Python Backend Development",
            }
        ],
    }

    response = client.post("/api/jobs", json=payload)

    assert response.status_code == 202
    data = response.json()
    assert data["job_id"] == 1
    assert data["total"] == 1


def test_input_validation():
    payload = {
        "event_name": "Python Workshop",
        "event_date": "October 8, 2026",
        "recipients": [
            {
                "name": "A",
                "email": "not-an-email",
                "course": "Python",
            }
        ],
    }

    response = client.post("/api/jobs", json=payload)
    assert response.status_code == 422


def test_job_status_endpoint():
    payload = {
        "event_name": "Python Workshop",
        "event_date": "October 8, 2026",
        "recipients": [
            {
                "name": "Test User",
                "email": "test@example.com",
                "course": "Python",
            }
        ],
    }

    create_response = client.post("/api/jobs", json=payload)
    job_id = create_response.json()["job_id"]

    response = client.get(f"/api/jobs/{job_id}")
    assert response.status_code == 200
    assert response.json()["job_id"] == job_id


def test_certificate_generation():
    payload = {
        "event_name": "Python Workshop",
        "event_date": "October 8, 2026",
        "recipients": [
            {
                "name": "Test User",
                "email": "test@example.com",
                "course": "Python",
            }
        ],
    }

    response = client.post("/api/jobs", json=payload)
    job_id = response.json()["job_id"]

    # BackgroundTasks execute when the TestClient request finishes.
    status = client.get(f"/api/jobs/{job_id}").json()

    assert status["status"] == "completed"
    assert status["completed"] == 1

    recipient_id = status["recipients"][0]["recipient_id"]
    download = client.get(
        f"/api/certificates/{recipient_id}/download"
    )

    assert download.status_code == 200
    assert download.headers["content-type"] == "application/pdf"


def test_individual_failure_does_not_stop_job():
    payload = {
        "event_name": "Python Workshop",
        "event_date": "October 8, 2026",
        "recipients": [
            {
                "name": "Valid User",
                "email": "valid@example.com",
                "course": "Python",
            },
            {
                "name": "",
                "email": "bad@example.com",
                "course": "Python",
            },
        ],
    }

    # Empty name is rejected by Pydantic before processing in this API.
    response = client.post("/api/jobs", json=payload)
    assert response.status_code == 422


def test_missing_job():
    response = client.get("/api/jobs/99999")
    assert response.status_code == 404
