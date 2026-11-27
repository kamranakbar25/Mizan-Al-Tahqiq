# Mizan Al-Tahqiq — Phase 0 Architecture Decision Record

**Status:** Closure addendum — decisions recorded from the verified local development state  
**Date:** 2026-11-27  
**Scope:** Phase 0 only. This document records the current foundation; it does not approve or implement the full Phase 1 architecture.

## 1. System identity and architectural direction

Mizan Al-Tahqiq is a private, evidence-first Sunni Islamic scholarly research platform. The permanent research scope and controlled phase sequence are defined by the Master Development Roadmap. The application is being developed as a modular Django system with a server-rendered/web API foundation and a vanilla HTML/CSS/JavaScript frontend.

**Decision:** Preserve a modular monolith as the current application shape. Do not split into microservices merely for architectural fashion. Extract independently deployable services only when a measured operational or scaling need justifies it.

## 2. Current foundation — verified facts

| Area | Recorded decision / current state | Evidence status |
|---|---|---|
| Backend | Python and Django 5.2 | Verified by project checks reported 2026-11-27 |
| Primary relational database | PostgreSQL; active local database `mizan_al_tahqiq` | Verified by Django connection output |
| Local AI runtime | Ollama accessed through a dedicated `ai_runtime` service boundary | Health endpoint/API reachable; `qwen3:4b` and `qwen3-embedding:0.6b` were listed |
| Vector infrastructure | Qdrant is part of the local development architecture; vector retrieval integration remains planned work | Infrastructure/configuration previously checked; do not infer production readiness |
| Frontend | HTML, CSS and vanilla JavaScript | Roadmap requirement |
| OCR | Previous OCRJob runtime retired; historical migrations retained; new OCR engine belongs to Phase 3 | Active-code grep returned no OCRJob references; only historical migrations remain |
| Ingestion | `library/services/universal_ingestion.py` is the current ingestion service boundary | Recorded project inspection; supported formats and exact internal behavior remain implementation details |
| Background processing | Database-backed ingestion jobs with transactional row locking and stale-job recovery | Regression tests cover simulated stale-job recovery; real process-kill drill remains outstanding |
| Backups | PostgreSQL custom-format backup and isolated restore procedure | Backup archive validation and isolated restore succeeded |
| Local corpus state | Scholarly library tables are intentionally empty after clearing demo records | Confirmed by project owner; checked model counts returned zero |
| Media | Django `MEDIA_ROOT` exists and is empty at this audit | Verified: 0 files, 0 bytes |

## 3. Architecture decisions

### ADR-001 — Modular Django application

Keep Django as the application core and organise domain capabilities into apps and service boundaries. Avoid introducing distributed services until there is a concrete requirement. This reduces deployment and debugging complexity during the foundation and corpus-building stages.

### ADR-002 — PostgreSQL is the authoritative structured-data store

Use PostgreSQL for durable relational records, identity, metadata, processing state, provenance and audit events. Do not treat the vector index, local model files, or generated answers as authoritative scholarly records. Any future search/vector index must be rebuildable from governed source records.

### ADR-003 — Preserve source identity and provenance

The system must preserve original source documents and distinguish source metadata, editions, extracted content, processing history and verification history. Source provenance and rights/licence information are first-class governance concerns. Never silently replace original source bytes or original text with corrected or normalised output.

The current foundation includes scholarly-library and source-governance model families (including Book, Edition, Document, Page, ExtractionVersion, TextBlock, SourceRecord, KnowledgeCategory and SourceVerificationEvent). This record intentionally does not assert a complete entity relationship diagram: exact FK/cardinality constraints must be reviewed against the current `library/models.py` before Phase 1 schema design is approved.

### ADR-004 — OCR is a separate future subsystem

The previous OCRJob model/runtime was retired through migration. Historical migrations are immutable history and must remain. No active OCRJob references were found in the checked application paths. OCR itself is not abandoned: the replacement digitisation/OCR engine is Phase 3 and must be independently designed, benchmarked and auditable.

### ADR-005 — Local AI runtime behind an adapter boundary

Application code should communicate with Ollama through the `ai_runtime` service layer rather than scattering direct HTTP calls throughout domain apps. Model availability and inference health are runtime facts, not guarantees of scholarly correctness. Retrieval, citations, evidence classification and answer verification belong to later research/AI phases.

The local endpoint was reachable at audit time. The observed installed models were `qwen3:4b` and `qwen3-embedding:0.6b`; model selection and evaluation remain subject to benchmark and scholarly task testing.

### ADR-006 — Vector search is supplemental, not canonical

Qdrant is planned as the vector retrieval store. PostgreSQL remains the source of truth for entities and provenance. Vector records must retain stable links to source records/passages and be reproducible through versioned indexing. Do not claim semantic search is complete merely because Qdrant is running.

### ADR-007 — Authentication and permissions are enforced server-side

Authentication and authorisation must be enforced by Django middleware, views and API permissions. Hiding frontend controls is not a security boundary. Separate admin/researcher sessions have been implemented and tested in the current development foundation. Permission policy still requires a dedicated role/action matrix before production.

### ADR-008 — Environment-specific configuration

Secrets and environment-specific values must come from environment configuration; real `.env` files and private source documents must not enter Git. `.env.example` is a safe template, not a secret. The current `DEBUG=True` and non-secure-cookie values describe local HTTP development only. Production requires separate hardened settings, HTTPS, secure cookies, proxy configuration, secret management and deployment testing.

### ADR-009 — Original files live outside the relational backup

PostgreSQL dumps do not include bytes in `MEDIA_ROOT` or external source directories. File storage must be backed up separately and restored consistently with its database state. The current media directory is empty, so media restore has not yet been exercised.

### ADR-010 — Background work must be recoverable and observable

Job claiming uses transactional row locking. Stale jobs are retried up to the configured attempt limit and then failed. Current regression tests simulate stale states; a real worker termination/restart drill and validation of the 30-minute stale threshold against maximum legitimate ingestion duration remain future operational gates. A heartbeat/lease design may be required if jobs can exceed that threshold.

## 4. Explicitly deferred to Phase 1 or later

The following are not claimed as complete by this Phase 0 record:

- Full domain-driven application map and master entity/relationship model.
- Final source, citation, book, edition, volume and passage schema.
- Full data-governance policy and lifecycle.
- Final role/permission matrix.
- File storage architecture for a large scholarly corpus.
- Search orchestration, multilingual embeddings, hybrid retrieval and reranking.
- Qdrant collection design, indexing lifecycle and evaluation.
- Knowledge graph storage and provenance model.
- Production task queue/worker architecture decision.
- Full audit/event taxonomy across all research domains.

These decisions must be made in Phase 1 before expanding research features. Do not treat this ADR as a substitute for the Phase 1 architecture deliverable.

## 5. Phase 0 operational caveats

- 37 automated tests passed; Django system check was clean; migration drift check reported no changes.
- PostgreSQL custom archive validation and isolated restore succeeded; 27 public base tables were present in both databases.
- The restore drill compared table counts and migration history, not every row, sequence, media object or Qdrant collection.
- A real process-kill worker recovery drill has not been performed.
- Linux production deployment and production security configuration have not been tested.
- Current database records are intentionally empty after demo-data removal. This is an expected clean-corpus starting state, not a failed preservation check.
- The current Git working-tree changes still require review before commit/push. A `git diff --stat` is not sufficient to approve deletions, migrations or untracked files.

## 6. Change control

Any change to these decisions must be recorded with: context, decision, alternatives considered, consequences, affected phase, migration/rollback implications, and tests. Do not silently alter the master roadmap or phase order.
