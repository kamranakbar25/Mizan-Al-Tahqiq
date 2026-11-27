# Task Processing, Audit and Operational Architecture

## Processing job model
Current code uses `ProcessingJob` with status, attempts, progress, error/result and timestamps. Claiming uses transactional `select_for_update(skip_locked=True)`. Current stale recovery uses a fixed 30-minute threshold based on `started_at`; tests cover simulated stale states, not a real worker kill/restart drill.

### Target job fields
`id`, `job_type`, `target_type`, `target_id`, `status`, `priority`, `idempotency_key`, `input_version`, `attempt_count`, `max_attempts`, `worker_id`, `claimed_at`, `heartbeat_at`, `lease_expires_at`, `progress_current`, `progress_total`, `result`, `error_code`, `error_message`, `created_at`, `started_at`, `finished_at`.

### Lifecycle
`queued → claimed/running → completed | partial | failed | cancelled`.
- Permanent input/permission/format failures are not retried.
- Transient runtime failures use bounded retry with backoff.
- Every attempt is recorded.
- A worker periodically heartbeats; lease expiry is the basis for reclaim.
- A worker may only complete a job if it still owns the lease/token.
- Idempotency prevents duplicate outputs when a job is retried.
- Long tasks (OCR, embeddings) report progress by page/batch.

### Transactional outbox
When a committed TextVersion must be indexed, write an outbox event in the same DB transaction. A worker publishes/indexes it and marks it complete. This prevents a committed text update from being missed if the process crashes between DB commit and enqueue.

### Queue technology decision
Keep DB-backed jobs at current scale. Do not add Redis/Celery until measured concurrency, scheduling, throughput or worker isolation needs justify it. If introduced later, PostgreSQL remains authoritative for job/result state.

## Audit event model
`AuditEvent`: actor, action, object type/id, before/after summary, reason, request/correlation ID, timestamp. Sensitive fields are redacted. Event rows are append-only for normal application roles; corrections create a new event referencing the prior event.

### Distinct event families
- acquisition event;
- rights decision event;
- source verification event;
- processing attempt/task event;
- text review decision;
- scholarly assessment;
- access/role grant or revocation;
- AI execution/retrieval trace;
- general user/system audit event.

Do not conflate:
- OCR success with text correctness;
- text approval with source authenticity;
- source authenticity with rights permission;
- AI answer citation with scholarly approval.

## Monitoring and recovery
Monitor queued job age, active lease age, retry count, failure rate, pages/minute, OCR/embedding latency, outbox backlog, index freshness, Qdrant health and DB connection saturation. Alert on expired leases, repeated failures, unprocessed outbox events and missing source file checksums.

Backups: PostgreSQL + original file store + metadata manifest. Qdrant is rebuildable. Restore test must compare schema/migrations, key table counts/checksums, file assets and selected citations. Keep recovery runbook separate from application code.
