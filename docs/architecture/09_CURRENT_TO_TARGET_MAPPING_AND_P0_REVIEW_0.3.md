# 09 — Current-to-Target Mapping and P0 Review
**Version 0.4 | Reconciled after owner approval | 27 November 2026**

## Evidence boundary
This mapping is based on the supplied `Mizan-Al-Tahqiq_SAFE_AUDIT_20261127_121650.zip` source snapshot and the Phase 1 review pack. It is not live PostgreSQL introspection and does not prove the deployed runtime matches the snapshot. Treat all target items as design proposals until owner-approved.

## A. Current physical model → target concept

| Current model / field family | Target concept | Mapping treatment | Key rule / unresolved point |
|---|---|---|---|
| `Author` | `Person` + `PersonName` | Preserve Author PK; additive identity mapping to Person | Never merge on name similarity alone |
| `Publisher` | `Publisher` | Retain canonical publisher identity | Add authority/alternate names only if needed |
| `Book` | `Work` | Retain existing table/PK during compatibility period | Work is intellectual creation, not a particular edition |
| `Book.authors` | `WorkContributor` | Replace conceptual M2M with role-bearing join additively | Preserve author order and uncertain attribution |
| `Edition` | `Edition` + `EditionContributor` | Retain; normalize editor/translator free text over time | Do not classify edition editor as Work author |
| `Volume` | `Volume` | Retain | Enforce Work/Edition/Volume ancestry consistency |
| `KnowledgeCategory` | `KnowledgeCategory` / taxonomy | Retain | Taxonomy is classification, not scholarly assertion |
| `SourceRecord` | `SourceRecord` | Retain and expand governance links | Source identity is distinct from stored file |
| `SourceVerificationEvent` | `SourceVerificationEvent` | Retain; formalize event taxonomy | Verification is not rights clearance or textual review |
| `Document.file` | `FileAsset` + `Document` | Add FileAsset; keep FileField during transition | No moving/deleting existing files in first migration |
| `Document.sha256`, `file_size`, `format`, metadata | `FileAsset` metadata + Document provenance | Copy/dual-read then reconcile | Same bytes do not imply same provenance |
| `Document.book/edition/volume` | Work/Edition/Volume relationship | Retain then add consistency validation | Current independent FKs can contradict |
| `Page` | `ContentUnit` (initial subtype: PDF page) | Keep Page table as compatibility representation | Do not force EPUB sections/folios into PDF-only assumptions |
| `Page.extracted_text` | selected-current-text projection | Keep temporarily as compatibility projection | Must not become independent canonical text |
| `ExtractionVersion` | `TextVersion` compatibility lineage | Retain and map version kind/derivation | Immutable versions; never overwrite OCR history |
| `TextBlock` | version-bound `TextBlock` | Retain; add offsets/order/geometry where absent | Offsets are valid only for exact version |
| `ReviewRecord` | `TextReviewDecision` | Retain then separate decision from corrected text | Review points to exact version reviewed |
| `IngestionRun` | `IngestionRun` / workflow orchestration | Retain; clarify run vs job | Run is a batch/process context, not worker lease |
| `ProcessingJob` | `WorkflowJob` + `JobAttempt` + lease | Retain current queue; add lease/heartbeat later | Existing started_at stale threshold is not heartbeat |
| `ai_runtime` Ollama service | `AIProvider` adapter boundary | Retain adapter | Model output is unverified, never authority |
| DRF sessions/middleware | account/session boundary | Retain and document | Separate admin/researcher cookies are not a full RBAC system |

## B. Target entities not present as first-class current models
`FileAsset`, `Person`, `PersonName`, `WorkContributor`, `EditionContributor`, `SourceAcquisition`, `RightsRecord`, `RightsDecisionEvent`, `ContentUnit`, `TextVersion`, `Passage`, `Citation`, `CitationLocator`, `ResearchEntity`, `EntityAlias`, `EntityIdentifier`, `EntityRelationship`, `ScholarlyAssertion`, `AssertionEvidence`, `AssertionAssessment`, `ResearchRun`, `RetrievalEvidence`, `AIExecutionTrace`, `JobAttempt`, `JobLease/heartbeat`, `OutboxEvent`, and append-only cross-domain `AuditEvent`.

These are target concepts, not a directive to create all tables in Phase 1. Domain-specific Quran, Tafsir, Hadith, Fiqh, Aqidah, Tasawwuf, History, Linguistics and Manuscripts entities are planned extensions, not current implementation claims.

## C. P0 contracts — recommended disposition
| Contract | Recommendation | Approval status |
|---|---|---|
| P0-01 Canonical text lifecycle | Immutable, version-bound text lifecycle; Page remains compatibility unit | APPROVED (owner record 2026-11-27) |
| P0-02 File identity/storage | Additive FileAsset; retain Document.file until migration proof | APPROVED (owner record 2026-11-27) |
| P0-03 Bibliographic identity | Person + role-bearing contributor records; preserve IDs | APPROVED (owner record 2026-11-27) |
| P0-04 Source governance | Separate source, acquisition, rights and verification records | APPROVED (owner record 2026-11-27) |
| P0-05 Citation locator | Scheme-specific locators tied to exact text version where applicable | APPROVED (owner record 2026-11-27) |
| P0-06 Document ancestry | Work → Edition → Volume → Document integrity validation | APPROVED (owner record 2026-11-27) |

## D. Non-destructive migration sequence (future implementation planning only)
1. Freeze current schema inventory and take verified DB + media backups.
2. Add target tables/nullable FKs only; do not rename/drop current fields.
3. Backfill deterministic mappings with an explicit mapping report.
4. Quarantine ambiguous author/person, source and ancestry mappings for review.
5. Dual-write or controlled compatibility service; avoid uncontrolled dual writes from views.
6. Reconcile counts, checksums, FK integrity and representative citations.
7. Switch reads only after acceptance tests pass.
8. Retain rollback window; remove legacy fields only in a separately approved later phase.

## E. Remaining verification gates (not owner-approval blockers)
- Reconcile the live PostgreSQL schema and applied migration graph; the uploaded ZIP is only a source snapshot.
- Execute the 12-module roadmap traceability matrix in `19_MASTER_ROADMAP_TRACEABILITY_0.6.md`.
- Confirm the merged repository contains this approved document set and that no stale duplicate documents supersede it.
- Finalize numeric retention, backup RPO/RTO and operational confidence thresholds before the relevant corpus-ingestion/production gates. These are deliberately deferred operational policy values, not unresolved Phase 1 architecture direction.

P0-01 through P0-06 are approved. D-01 through D-12 are approved in the owner record. Do not ask the owner to approve these again.
