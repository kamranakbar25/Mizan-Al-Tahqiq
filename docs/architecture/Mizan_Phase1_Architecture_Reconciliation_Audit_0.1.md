# Mizan Al-Tahqiq — Phase 1 Architecture Reconciliation Audit

**Version:** 0.1  
**Review basis:** `Mizan-Al-Tahqiq_SAFE_AUDIT_20261127_121650.zip` and `Mizan_Phase1_Complete_Architecture_Baseline_1.0.zip`  
**Review type:** Static source-to-target architecture comparison  
**Code/database changes:** None  
**Runtime/environment checks:** Not performed (per project-owner instruction)

## 1. Executive result

The Phase 1 architecture baseline is directionally compatible with the existing Django modular monolith and preserves the current `library` and `ai_runtime` foundations. It is **not yet implementation-ready or approved for migration**. The target architecture introduces several foundational entities and invariants that do not exist in the current schema, and some existing fields currently combine concerns that the target separates.

The current source snapshot contains 15 `library` models and no database models in `ai_runtime`. The existing system is a digital-library/ingestion foundation, not yet the full scholarly research data platform. This is consistent with the roadmap's phased implementation strategy.

## 2. Existing-to-target model mapping

| Existing model | Target concept | Reconciliation decision / gap |
|---|---|---|
| `Author` | `catalog_person` + `catalog_person_name` | Preserve existing Author rows/PKs. Plan additive Person identity and alternate-name model; migrate authorship through contributor relations without dropping current M2M prematurely. |
| `Book` | `catalog_work` + `catalog_work_title` | Keep physical `Book` table initially; document its domain meaning as Work. Existing title fields are useful but title variants are not fully normalized. |
| `Book.authors` M2M | `catalog_work_contributor` | Current relation has no contributor role, attribution status, ordering, or source citation. Add explicit contributor relation in a later additive migration. |
| `Publisher` | `catalog_publisher` | Existing fields are minimal (`name`, `location`). Add aliases/identifiers and richer imprint metadata only where the schema requires them. |
| `Edition` | `catalog_edition` | Existing publication/editor/translator fields are useful. `editor` and `translator` are free-text, not linked contributor identities; publication year is text and should remain source-faithful until normalized. |
| `Volume` | `catalog_volume` | Basic edition/volume relation exists. Printed page range is text; keep separate from PDF page indexing. |
| `SourceRecord` | `sources_source_record` + `sources_rights_record` + `sources_acquisition` | Current model combines source identity, rights state, verification state and acquisition date. Target separates them. `accessed_at` is not a full acquisition chain-of-custody record. |
| `SourceVerificationEvent` | `sources_verification_event` + rights decision events | Existing event records both verification and rights before/after values, but it is not enforced append-only and the target needs independent rights and source-verification histories. |
| `Document.file` | `library_file_asset` + `library_document` | Current direct `FileField` is a coupling point. Target FileAsset/storage adapter should be introduced additively; retain current path and checksum while migrating references safely. |
| `Document` | `library_document` | Existing metadata is a useful base. Work/Edition/Volume FKs are independent and can contradict each other; target invariant requires consistent ancestry. |
| `Page` | `corpus_content_unit` | Current model is PDF-page-shaped. Target must generalize to PDF pages, EPUB sections, folios and other locators. Existing `pdf_page_index` (0-based), `pdf_page_number` (1-based), and printed page label must remain distinct. |
| `Page.extracted_text` + `ExtractionVersion` | `corpus_text_version` | Current text is duplicated between Page and versioned extraction. Define one canonical versioned-text contract and treat Page text as compatibility/legacy data during transition. |
| `TextBlock` | `corpus_text_block` | Existing block model is a useful base but needs language/script/direction and robust source offsets/locator semantics as defined by final requirements. |
| — | `corpus_passage` | Missing. Required for stable citation, search, embedding and AI evidence units. |
| `ReviewRecord` | `corpus_review_decision` | Current record stores `reviewed_text` on the review record. Target separates decision from text: a correction should create a new TextVersion, not overwrite/couple the review decision to text. Append-only behavior is not enforced. |
| — | `citations_citation` + `citations_locator` | Missing. Exact source/version/printed-page/PDF-index/folio/section/line locators are foundational and must be designed before scholarly answer features. |
| — | `research_research_entity`, aliases, identifiers, relationships | Missing. Needed for canonical entities across Quran, Hadith, Fiqh, Tasawwuf, history and linguistic research. |
| — | `research_scholarly_assertion`, evidence, assessment | Missing. Needed to preserve attribution, disagreement, evidence and scholarly assessment separately. |
| Django default user | `accounts_role`, permission, assignment tables | No custom user model is present in the snapshot. Keep Django `AUTH_USER_MODEL`; add role/grant models around it rather than replacing user identity. |
| `ProcessingJob` + `IngestionRun` | `workflows_processing_job`, attempt, outbox | Current queue is document-only, with attempts/progress but no heartbeat, lease, idempotency key, attempt history or outbox. Existing 30-minute stale threshold is a known operational limitation. |
| — | `governance_audit_event` | Missing. Source verification events alone do not provide cross-domain audit coverage. |
| — | Search and AI persistence tables | Missing. Qdrant is configured in Compose, but the source snapshot does not show an implemented semantic indexing/retrieval lifecycle or persisted research-run/claim/citation records. |

## 3. Confirmed current implementation facts

- Django 5.2 project with `library` and `ai_runtime` apps.
- `library/models.py` defines: Author, Publisher, Book, Edition, Volume, KnowledgeCategory, SourceRecord, SourceVerificationEvent, Document, Page, IngestionRun, ProcessingJob, ExtractionVersion, TextBlock and ReviewRecord.
- `ai_runtime/models.py` has no database models.
- `ai_runtime/services/ollama.py` provides local health/model listing, chat generation and embeddings behind an adapter boundary.
- Ingestion currently supports PDF, TXT, DOCX and EPUB; extraction versions and text blocks are created from extracted page/unit text.
- The worker claims queued jobs with PostgreSQL row locking (`select_for_update(skip_locked=True)`) and uses a fixed 30-minute stale threshold based on `started_at`.
- Current REST defaults require authentication. Source rights/verification mutation is additionally gated by `is_staff` in the serializer; a full role/action/object policy matrix is not present.
- Current session middleware uses separate admin and researcher cookie names.
- The migration history in the snapshot contains `library` migrations 0001–0005 and historical `ai_runtime` migrations 0001–0003. Historical migrations must remain immutable.
- The current `.gitignore` excludes `.env`, virtual environments, `media/`, `data/`, `_project_admin/`, logs, backups, PDFs and EPUBs.

## 4. Architecture decisions to retain

1. Keep the modular Django monolith; do not split into microservices.
2. Keep PostgreSQL as the authoritative structured-data store.
3. Preserve existing BigAutoField IDs and the existing Document UUID; do not perform a global PK conversion.
4. Keep the physical `Book` model/table initially while documenting it as the Work concept.
5. Keep existing `library` and `ai_runtime` apps operational; create future domain apps only when their roadmap phase begins.
6. Keep Ollama behind the `ai_runtime` adapter. Model output remains non-authoritative.
7. Keep Qdrant as a derived/rebuildable index, never the canonical scholarly store.
8. Use additive migrations and compatibility periods. No destructive table/field changes without explicit approval and a tested data migration/rollback plan.

## 5. Blocking design clarifications before Phase 1 approval

### P0 — Required before schema approval

- **Canonical text lifecycle:** Decide the precise transition from `Page.extracted_text` + `ExtractionVersion` to `ContentUnit` + `TextVersion` + `Passage`, including how old extraction versions and text blocks remain addressable.
- **File identity and storage:** Specify whether one FileAsset can back multiple Documents, whether a Document always points to one original asset, how duplicate checksums are represented, and how current `FileField` paths migrate without moving/deleting bytes.
- **Bibliographic contributor model:** Define Person identity, contributor roles, ordering, uncertain/anonymous authorship, and how existing Author M2M rows map.
- **Source governance split:** Define the exact lifecycle and ownership of SourceRecord, SourceAcquisition, RightsRecord and their independent event histories. Avoid treating a single SourceRecord status as both provenance verification and legal permission.
- **Citation locator contract:** Define mandatory locator fields and validation rules for printed page, PDF page index/number, folio recto/verso, section, line and exact TextVersion/Passage.
- **Document ancestry integrity:** Define how `Document.book`, `edition`, and `volume` are validated and how inconsistent legacy combinations are handled.

### P1 — Required in the Phase 1 design package

- **Review and scholarly assessment separation:** Define distinct text-review decisions, scholarly assertions, evidence links and assessments. A textual correction must create a new version.
- **Role and scope matrix:** Define roles, permissions, object scopes, admin/researcher separation, and staff/superuser behavior without replacing Django's user model.
- **Workflow contract:** Define job types, idempotency, heartbeat/lease, attempts, retry policy, terminal failure, outbox and worker observability.
- **Audit taxonomy:** Define append-only event families and which actor/reason/correlation fields each requires.
- **Search/AI persistence:** Define index versioning and exact TextVersion binding; AI research run, retrieved evidence, generated answer, claim and citation traceability.
- **Metadata missingness:** Define field-state representation (`known`, `unknown`, `not_applicable`, `not_checked`, `disputed`) and which metadata fields require it.

## 6. Target schema quality notes

These are design clarifications, not reasons to change code now:

1. Target schema uses UUIDs for new scholarly identities while existing entities use BigAutoField. The master architecture correctly says to preserve existing IDs; each FK mapping must therefore state whether it references an existing bigint identity or a new UUID identity. Do not infer that all target FKs are UUIDs if they reference existing Author/Book/Publisher rows.
2. `catalog_person` and existing `Author` need an explicit identity-mapping plan; avoid creating duplicate people when the same scholar appears as author, narrator, editor or historical person.
3. `Document` and `FileAsset` need an explicit cardinality and uniqueness policy. A checksum uniqueness rule should not accidentally prevent multiple bibliographic records from referring to the same digital file/source witness.
4. Source rights, source verification and text review must be independent state machines and event streams. The current combined `SourceVerificationEvent` should be treated as legacy transition evidence, not the final event contract.
5. The target schema's `TextVersion`/`Passage` invariants need a stable rule for passage IDs across resegmentation or revised text versions; old citations must never silently point to changed text.
6. The target schema should state which specialized domain tables are Phase 1 logical contracts versus later-phase implementation. They must not be created in the database during Phase 1.

## 7. Scope and evidence limitations

- This review is static and based on the two uploaded ZIP snapshots, not the user's live working tree.
- No live PostgreSQL schema introspection was performed; migration files were reviewed, but actual applied migration state and DB constraints remain unverified here.
- No environment, `.env`, Ollama, Qdrant, test-suite or runtime health checks were performed, as instructed.
- The uploaded safe-audit ZIP contains original book PDFs and local Qdrant storage data in addition to source code. The `.gitignore` excludes `data/` and PDFs/EPUBs, but this ZIP itself should not be committed or uploaded to a public repository.
- The exact Master Development Roadmap document was not included in the source ZIP; the Phase 1 12-module scope used here is the locked scope already established by the project owner in prior project discussion.

## 8. Recommended Phase 1 completion sequence

1. Resolve the six P0 design contracts above in the architecture documents.
2. Update the master schema and ERDs to reflect the approved decisions; keep all domain-specific tables as future-phase contracts only.
3. Produce a field-by-field migration map from current models/migrations to target entities, including legacy compatibility and rollback notes.
4. Produce the role/action/object permission matrix, workflow state diagram and audit event matrix.
5. Trace every one of the 12 Phase 1 modules to a document section, schema entities, decisions and exit criteria.
6. Obtain project-owner approval. Only then mark Phase 1 closed. No implementation migration is part of this phase.

**Current disposition:** Architecture baseline drafted; reconciliation audit completed against the uploaded source snapshot; Phase 1 remains **in progress — design decisions and owner approval pending**.
