# Mizan Al-Tahqiq — Phase 1 Current-to-Target Mapping & P0 Decision Review 0.2

**Status:** Consolidated technical review draft — NOT Phase 1 closure  
**Evidence base:** SAFE_AUDIT source ZIP snapshot dated 2026-11-27, Phase 1 Consolidated Review Pack 0.2, P0 Contracts 0.1, and the Phase 1 architecture documents.  
**Important limitation:** This is a source-code snapshot review. It does not independently inspect the live PostgreSQL database, current GitHub branch, local uncommitted changes, media files, or running services. No implementation change is authorized by this document.

## 1. Executive result

The current project is a working Django modular-monolith foundation, not yet the complete scholarly research data platform. The existing `library` app provides bibliographic records, source provenance, document upload, page extraction, extraction versions, text blocks, review records, ingestion runs, and processing jobs. `ai_runtime` currently has no database models and is an Ollama integration boundary.

The target architecture is directionally compatible with the current code, but it is a **substantial additive domain expansion**, not a direct rename of existing models. Preserve current IDs and ingestion history; introduce new canonical abstractions gradually and maintain compatibility until a separately approved migration plan exists.

## 2. Current → target mapping

| Current model / capability | Evidence in snapshot | Target concept | Recommended disposition | Main gap / migration caution |
|---|---|---|---|---|
| `Author` | Name, Arabic name, biography, birth/death year | `Person` + role-bearing work/edition contributors | Retain as legacy-compatible identity; map to Person in a later additive migration | Author is currently directly attached to Book via M2M; target needs roles, attribution certainty, dates and source evidence. Do not merge uncertain attributions. |
| `Book` | Titles, aliases, language, description, subject, categories, authors | `Work` | Treat Book as current Work-equivalent; preserve PKs | Name mapping only; target needs stable identifiers, work-level metadata and explicit contributor relationships. |
| `Edition` | Book FK, publisher, year, place, editor/translator strings, ISBN | `Edition` + EditionContributor | Retain; normalize editor/translator strings into contributor links only when verified | Free-text names cannot be automatically converted into people without authority control/review. |
| `Volume` | Edition FK, volume number, printed page range | `Volume` | Retain | Add ancestry consistency checks for Document→Book/Edition/Volume; existing model permits mismatched combinations. |
| `Publisher` | Name, location | `Organization` / Publisher authority record | Retain initially; map to organization later | Publisher is currently a narrow entity; avoid premature universal organization conversion. |
| `KnowledgeCategory` | Hierarchical taxonomy | Subject taxonomy / knowledge domain | Retain | Add governance for taxonomy versioning, multilingual labels and controlled vocabularies. |
| `SourceRecord` | Type, org, URL, external ID, license, rights and verification fields | `SourceRecord` + `SourceAcquisition` + `RightsRecord` | Retain SourceRecord; split lifecycle concepts additively | Current record mixes source identity, acquisition/access and rights. Existing status fields are mutable; event log captures some transitions only. |
| `SourceVerificationEvent` | Append-style event rows for verification and rights changes | Separate verification and rights event streams | Retain as historical event; extend or supersede with typed events | Current event requires both verification and rights values on every event; rights and scholarly verification are distinct decisions. |
| `Document.file` | Django FileField; original filename, SHA-256, size | `FileAsset` + bibliographic/witness `Document` | Preserve FileField compatibility; introduce FileAsset as a logical asset registry first | Do not move/delete bytes during first schema migration. Distinguish byte identity from bibliographic witness/provenance. |
| `Document` | Book required; Edition/Volume optional; source link; format/status/metadata | `Document` / SourceWitness linked to Work, Edition, Volume and FileAsset | Retain and extend | `book` currently cascades; target needs safer archival retention and consistent ancestry. Define delete/retention policy before FK changes. |
| `Page` | PDF index/number, printed page, label, geometry, extracted text, status | `ContentUnit` | Keep Page as PDF-specific subtype/legacy table; introduce generalized ContentUnit | Target must support EPUB sections, manuscript folios, images and non-PDF units. Keep PDF page index distinct from printed page and folio. |
| `ExtractionVersion` | Page FK, version, embedded/OCR/manual source, engine, text, hash, quality | Immutable `TextVersion` / extraction artifact | Map as current extraction-version record; preserve PK/history | Avoid destructive rename. Clarify raw OCR, corrected transcription, normalization, transliteration and translation as separate version kinds. |
| `TextBlock` | Extraction FK, order, type, text, language, bounding box | Version-bound `TextBlock` / `Passage` | Retain and bind explicitly to immutable text version | Add stable anchors/offset semantics and ensure derived vectors cite exact version. |
| `ReviewRecord` | Extraction FK, status, reviewer, notes, reviewed_text | Textual review/approval event linked to exact version | Retain historical rows; target review must reference exact immutable version | `reviewed_text` stored separately can drift from extraction text; model approval/correction as a new version plus review decision. |
| `IngestionRun` | Per-document aggregate counts, status, report | `ProcessingRun` / pipeline execution | Retain | Need pipeline/config version, reproducibility, source file hash, task linkage and detailed per-stage outcomes. |
| `ProcessingJob` | DB queue, attempts, progress, status, timestamps, result/errors | Durable task + lease/heartbeat + idempotency + event history | Retain current queue as baseline; add operational guarantees later | Snapshot indicates no heartbeat/lease; stale timeout based on started_at can misclassify long jobs. Add heartbeat, lease expiry, idempotency key and retry policy before scale-up. |
| `ai_runtime` Ollama adapter | No DB models; health/models/chat/embeddings adapter | Provider-agnostic AI runtime + persisted research runs/evidence | Retain Ollama adapter behind provider interface | Persist model/provider/version, prompt/config, retrieval set, cited text versions, output and human assessment. AI output must not become scholarly verification automatically. |
| PostgreSQL | Authoritative relational database in project settings | Authoritative source of record | Retain | Confirm constraints/indexes against live migrations before implementation; this review cannot inspect live DB. |
| Qdrant | Planned/derived vector store in project architecture; not authoritative | Rebuildable semantic index | Keep derived and rebuildable | Every vector must reference exact source text version and embedding model/version; deletion/rebuild and stale-index policy required. |
| Authentication / permissions | Django default user; DRF IsAuthenticated; Session + Basic auth; separated admin/researcher session cookies | Scoped role/action/resource permissions | Retain Django auth foundation; add explicit permission matrix | IsAuthenticated is not a complete researcher/admin/reviewer/scholar permission model. Verify endpoint-level authorization and object scope before exposing research data. |

## 3. Six P0 contract recommendations

These are recommendations for owner decision, not approved changes.

### P0-01 — Canonical text lifecycle
**Recommend: APPROVE WITH CLARIFICATION.** Keep `Page` as the existing PDF locator and compatibility record. Introduce generalized `ContentUnit` for page, folio, EPUB section, image region and other source units. Treat `ExtractionVersion` as the current legacy extraction artifact and introduce immutable `TextVersion` semantics additively. `TextBlock`, Passage, review decisions and future embeddings must point to an exact immutable version. Raw OCR, corrected transcription, normalized Arabic, transliteration and translation are separate artifacts, not overwrites of one text field.

### P0-02 — File identity and storage
**Recommend: APPROVE.** Introduce `FileAsset` as byte identity (hash, size, media type, storage key, integrity state); keep `Document` as bibliographic/witness/provenance record. Preserve current `Document.file` during transition. Identical bytes may share an asset, but must not merge separate acquisition/provenance records. Original source bytes remain immutable/private; derivative OCR images and normalized outputs are separate assets.

### P0-03 — Bibliographic identity
**Recommend: APPROVE WITH CONSERVATIVE MIGRATION.** Treat current `Book` as Work-equivalent; retain its PK and relations. Introduce Person and role-bearing contributor relations for author, editor, translator, commentator, compiler, verifier and uncertain attribution. Map existing Author records only with deterministic preservation; convert free-text editor/translator values only after review. Keep Work, Edition and Volume separate.

### P0-04 — Source governance
**Recommend: APPROVE.** Keep SourceRecord as source/publisher/repository identity. Separate acquisition/access event (where/when/how obtained) from rights/licence/permission record and from scholarly source verification. Preserve current SourceVerificationEvent as legacy history; new event families should make rights decisions and verification decisions independently auditable. No ingestion should imply lawful reuse; unknown rights remain unknown.

### P0-05 — Citation and locator system
**Recommend: APPROVE.** Add Citation + CitationLocator with locator scheme and version binding. Printed page, PDF zero/one-based index, PDF displayed page, volume/page, folio/recto-verso, chapter/section, hadith number, Quran surah/ayah and line/paragraph are different locator types. A citation must resolve to a specific work/edition/volume/document/content unit and, where text is quoted, the exact TextVersion. Never silently treat PDF page index as printed page.

### P0-06 — Document ancestry integrity
**Recommend: APPROVE WITH NON-DESTRUCTIVE CONSTRAINTS.** Canonical hierarchy is Work → Edition → Volume → Document/Witness → ContentUnit. Existing Document has independent Book, Edition and Volume FKs and can represent inconsistent ancestry. Add validation/constraints only after legacy anomaly report; do not rewrite or delete records silently. Replace destructive cascade policies only through separately reviewed retention/migration design.

## 4. Additional architecture decisions required before Phase 1 closure

1. **Research identity model:** define authority control for persons, organizations, works, manuscripts, places and scholarly concepts; include aliases, identifiers, transliterations and confidence/provenance.
2. **Scholarly assertion model:** define assertion, evidence, assessment, assessor, school/madhhab/tradition, scope and disagreement representation. Distinguish a source's statement from a platform's editorial assessment.
3. **Domain modules:** approve boundaries and ownership for Quran/Tafsir, Hadith/Isnad, Fiqh/Usul/Madhhabs, Aqidah, Tasawwuf, Seerah/History, Arabic Linguistics and Manuscripts. Shared citations, persons, works, text versions and evidence remain cross-domain foundations.
4. **Permissions matrix:** enumerate role × action × resource scope, including admin, librarian, ingest operator, OCR reviewer, source-rights reviewer, scholar/researcher and read-only auditor. Define private-project boundary and audit of privileged actions.
5. **Search/index contract:** define lexical, trigram and semantic retrieval; language/script normalization; Arabic diacritics policy; chunk boundaries; embedding model/version; filters; ranking; citations; re-index and stale-vector handling.
6. **Research run/evidence persistence:** retain question, selected corpus snapshot, retrieval candidates, exact text versions, citations, model/provider/config, generated answer, human review and export history.
7. **Processing reliability:** define heartbeat/lease, idempotency, retries, dead-letter/manual recovery, cancellation, per-stage audit and reproducible pipeline versioning.
8. **Data retention and backup:** define retention, legal takedown, soft-delete/archive, immutable originals, derived-data rebuild, backup/restore scope including DB + media + vector index manifests.
9. **Operational security:** secrets, encryption at rest/in transit, upload malware scanning, private media delivery, rate limits, session/CSRF policy, admin isolation, logging redaction and threat model.
10. **Schema/migration strategy:** exact model/table/field mapping, nullability/defaults, constraints, indexes, backfill, dual-read/write period, rollback and acceptance tests.

## 5. Source-supported current-state observations

- `library/models.py` defines Author, Publisher, Book, Edition, Volume, KnowledgeCategory, SourceRecord, SourceVerificationEvent, Document, Page, IngestionRun, ProcessingJob, ExtractionVersion, TextBlock and ReviewRecord.
- `ai_runtime/models.py` explicitly states that the AI runtime currently has no database models.
- `DocumentSerializer` allows PDF, TXT, DOCX and EPUB uploads; enforces a 100 MB upload limit and performs signature/package checks.
- `Document` currently stores a direct FileField plus SHA-256 and file size; this is not yet a separate FileAsset registry.
- `Page` stores both `pdf_page_index` and `pdf_page_number`, plus a separate `printed_page_number`; these locator distinctions should be preserved.
- `ExtractionVersion` supports embedded, OCR and manual sources; it is versioned per Page. `TextBlock` references ExtractionVersion. `ReviewRecord` also references ExtractionVersion and stores reviewed_text.
- `ProcessingJob` has attempts/progress/status/timestamps, but no heartbeat or lease fields in the inspected model.
- DRF defaults to IsAuthenticated with SessionAuthentication and BasicAuthentication; this alone does not define the full target role/scope matrix.

## 6. Open owner decisions (one consolidated response)

Please confirm or amend these defaults in one pass:

| ID | Proposed default | Owner response needed |
|---|---|---|
| D1 | Approve P0-01 text lifecycle with additive ContentUnit + immutable TextVersion | Approve / Amend |
| D2 | Approve P0-02 FileAsset while retaining Document.file during transition | Approve / Amend |
| D3 | Approve P0-03 Book≈Work mapping; no automatic fuzzy author merges | Approve / Amend |
| D4 | Approve P0-04 independent acquisition, rights and verification lifecycles | Approve / Amend |
| D5 | Approve P0-05 scheme-specific, version-bound citations | Approve / Amend |
| D6 | Approve P0-06 hierarchy and legacy anomaly-first constraints | Approve / Amend |
| D7 | Approve PostgreSQL as system of record; Qdrant and embeddings remain derived/rebuildable | Approve / Amend |
| D8 | Approve modular Django monolith; no microservices until measured need | Approve / Amend |
| D9 | Approve AI outputs as research assistance only, never automatic scholarly verification | Approve / Amend |
| D10 | Approve preservation of original source files and full provenance chain | Approve / Amend |

## 7. Phase 1 exit gate — remaining evidence

Phase 1 must remain OPEN until all are complete:
- [ ] Master roadmap Phase 1 scope cross-checked against all 12 required modules.
- [ ] Current-to-target mapping reviewed against exact source code and migrations.
- [ ] Live PostgreSQL schema/migration state reconciled (not covered by this ZIP review).
- [ ] P0 decisions D1–D10 approved or amended by owner.
- [ ] Target schema/data dictionary and all ERDs agree with approved decisions.
- [ ] Domain boundaries and service contracts finalized.
- [ ] Source governance, rights, acquisition and verification workflows finalized.
- [ ] Full role/action/resource permission matrix finalized.
- [ ] Citation/locator and versioned text contracts finalized.
- [ ] Search/AI/research-run evidence contract finalized.
- [ ] Processing, audit, backup, retention, security and recovery workflows finalized.
- [ ] Decision register and risk register updated.
- [ ] Non-destructive migration strategy and rollback principles documented.
- [ ] Owner sign-off recorded.

## 8. Non-destructive implementation boundary

This document authorizes **no code, model, migration, settings, database, corpus, media, vector-index or runtime changes**. All future implementation must occur in its roadmap phase after architecture approval, with backups, migration plan, tests and explicit approval.
