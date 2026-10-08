# Bulk Certificate Generator

A FastAPI backend that accepts one bulk certificate-generation request, validates recipients, generates recipient-specific PDF certificates, tracks job progress, and provides download endpoints.

## Technology

- Python
- FastAPI
- SQLAlchemy
- SQLite (relational database)
- ReportLab for PDF generation
- Pytest for testing

## Design decision: background processing

The API uses FastAPI `BackgroundTasks`.

The client submits one request containing many recipients. The API creates a job and immediately returns the job information with HTTP `202 Accepted`. Certificate generation then runs in the background.

This keeps the API responsive and avoids forcing the client to wait for every PDF to be generated.

For very large production workloads, the same service layer can be moved to a queue such as Celery/RQ with Redis.

## Project structure

```text
bulk-certificate-generator/
├── app/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── routes/
│   │   ├── jobs.py
│   │   └── certificates.py
│   └── services/
│       ├── certificate_generator.py
│       └── job_processor.py
├── tests/
│   └── test_api.py
├── generated_certificates/
├── requirements.txt
└── README.md
```

## Setup

### 1. Create a virtual environment

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the API

```bash
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Interactive Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

## API endpoints

### Health

```http
GET /health
```

### Create bulk generation job

```http
POST /api/jobs
```

Example request:

```json
{
  "certificate_title": "Certificate of Completion",
  "event_name": "Python Workshop",
  "event_date": "October 8, 2026",
  "recipients": [
    {
      "name": "Akash Singh",
      "email": "akash@example.com",
      "course": "Python Backend Development"
    },
    {
      "name": "Rahul Kumar",
      "email": "rahul@example.com",
      "course": "Python Backend Development"
    }
  ]
}
```

The endpoint returns `202 Accepted`.

Example response:

```json
{
  "job_id": 1,
  "status": "queued",
  "total": 2,
  "completed": 0,
  "failed": 0,
  "progress_percent": 0,
  "created_at": "...",
  "updated_at": "...",
  "recipients": []
}
```

### Check job status

```http
GET /api/jobs/{job_id}
```

Example completed response:

```json
{
  "job_id": 1,
  "status": "completed",
  "total": 2,
  "completed": 2,
  "failed": 0,
  "progress_percent": 100,
  "created_at": "...",
  "updated_at": "...",
  "recipients": [
    {
      "recipient_id": 1,
      "name": "Akash Singh",
      "email": "akash@example.com",
      "status": "completed",
      "certificate_id": "CERT-1-ABC1234567",
      "error_message": null,
      "download_url": "/api/certificates/1/download"
    }
  ]
}
```

### Download one certificate

```http
GET /api/certificates/{recipient_id}/download
```

Returns a PDF.

### Download all generated certificates

```http
GET /api/certificates/job/{job_id}/download-all
```

Returns a ZIP file containing all successfully generated certificates.

## Testing

Run:

```bash
pytest -q
```

The tests cover:

- Creating a generation job
- Input validation
- Job status
- PDF certificate generation
- Certificate retrieval
- Missing-job handling

## Validation and failure handling

Pydantic validates the incoming request before a job is created.

Each recipient is processed independently. Certificate generation is wrapped in a separate `try/except`, so a failure for one recipient does not stop the remaining recipients.

The job stores:

- total recipients
- completed count
- failed count
- current job status
- per-recipient status
- per-recipient error message
- certificate ID
- generated file path

## Important implementation decisions

1. **One request for many recipients**
   - The API accepts an array of recipients.

2. **Relational database**
   - `generation_jobs` stores job-level information.
   - `recipients` stores individual generation results.

3. **Background processing**
   - The request returns quickly.
   - Generation happens after the request is accepted.

4. **Independent recipient processing**
   - One failed certificate does not stop the whole job.

5. **PDF generation**
   - ReportLab creates a single predefined certificate design.
   - Recipient-specific fields are inserted into that template.

6. **Production scaling**
   - For very large workloads, the `process_job` service can be moved from FastAPI BackgroundTasks to a durable task queue such as Celery/RQ.

## Interview explanation

The main flow is:

```text
POST /api/jobs
       ↓
Validate request with Pydantic
       ↓
Create GenerationJob + Recipient rows
       ↓
Return 202 Accepted
       ↓
Background processor
       ↓
Generate each PDF independently
       ↓
Update recipient status
       ↓
Update job counters
       ↓
GET /api/jobs/{id}
       ↓
Download certificate
```
