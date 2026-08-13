# Background workers (design, not wired up)

Document ingestion currently runs inline inside the upload request
(`DocumentService.upload_and_process`), which is fine for demo/portfolio use
but would block the request thread on large files in production.

The intended production design:

- **Broker**: RabbitMQ
- **Worker**: Celery, consuming an `ingest_document` task with the document ID
- **Flow**: `POST /documents/upload` saves the file, creates a `Document` row
  with status `pending`, enqueues `ingest_document.delay(document_id)`, and
  returns immediately. The Celery worker then does extraction/chunking/embedding
  and flips the status to `ready` or `failed`. The frontend polls
  `GET /documents/{id}` (already implemented) until status changes.

This isn't implemented in this codebase to keep the deliverable honest and
runnable without an extra broker dependency -- but the service layer is
already split (`_process_document`) so wiring it to a Celery task is a
same-day change, not a redesign.
