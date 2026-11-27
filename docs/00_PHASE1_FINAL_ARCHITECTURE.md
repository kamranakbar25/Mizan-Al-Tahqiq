# MIZAN AL-TAHQIQ
# PHASE 1 — SYSTEM ARCHITECTURE AND DATA GOVERNANCE
**Architecture baseline: 1.0 | Date: 27 November 2026 | Status: Complete design package for Phase 1 review**

## 1. Purpose and boundary

Phase 1 defines the complete target architecture and data model before expanding research features. It covers the twelve roadmap modules: domain-driven application structure; core database; research entities; source and citation; book and edition relationships; users and permissions; file storage; search; AI services; knowledge graph; task processing; audit and provenance.

This is a design deliverable, not a feature implementation. No source code, Django model, migration, database, storage or Qdrant configuration is changed by this package. The architecture deliberately preserves the existing modular Django monolith.

## 2. Architectural decisions at a glance

| Concern | Decision |
|---|---|
| Application shape | Modular Django monolith; domain boundaries and service contracts first. No microservices without measured need. |
| Backend | Existing Django 5.2 + DRF foundation retained. |
| Frontend | HTML, CSS and Vanilla JavaScript retained. |
| Authoritative database | PostgreSQL. SQLite fallback is development/test convenience only and must not be used for production corpus data. |
| Canonical source bytes | Immutable file assets in private storage, identified by SHA-256 and size. |
| Bibliography | Work → Edition → Volume; contributors represented with explicit roles. |
| Text | ContentUnit → TextVersion → TextBlock/Passage. Raw extraction, corrected transcription, normalized text, transliteration and translation are distinct representations. |
| Citation | Citation + CitationLocator; locator distinguishes printed page, PDF page index, folio, section, line and exact text version. |
| Research knowledge | Canonical ResearchEntity, typed relationships, attributed ScholarlyAssertion and AssertionEvidence. |
| Search | PostgreSQL lexical search first; Qdrant semantic index as derived/rebuildable infrastructure. |
| AI | Provider adapter boundary; current Ollama adapter retained. AI answers remain unverified outputs until separately assessed. |
| Knowledge graph | Relational graph in PostgreSQL first; graph DB deferred until workload proves need. |
| Background tasks | Existing DB-backed queue retained; add heartbeat/lease/idempotency before scaling. |
| Audit | Append-only decision and activity events; source verification, textual review and scholarly assessment remain distinct. |

## 3. Current implementation baseline (verified in uploaded source snapshot)

The uploaded source snapshot contains two Django apps: `library` and `ai_runtime`; Django admin, DRF, templates and static assets are present. `library/models.py` currently defines 15 models: Author, Publisher, Book, Edition, Volume, KnowledgeCategory, SourceRecord, SourceVerificationEvent, Document, Page, IngestionRun, ProcessingJob, ExtractionVersion, TextBlock and ReviewRecord. `ai_runtime/models.py` explicitly has no database models. The Ollama adapter supports local health, model listing, chat generation and embeddings.

Current `Document` stores a direct Django `FileField`, SHA-256, file size, format and metadata. `Page` stores PDF page index/number, optional printed page label and `extracted_text`; `ExtractionVersion` separately stores versioned text. `TextBlock` belongs to an ExtractionVersion. `ReviewRecord` stores reviewed text inside the review record. `Document.book`, `Document.edition` and `Document.volume` are independent FKs, so parent consistency is not enforced by the current model.

Current `ProcessingJob` uses a database row claim with `select_for_update(skip_locked=True)`, attempt count and a 30-minute stale threshold based on `started_at`; there is no heartbeat/lease field. Current source supports PDF/TXT/DOCX/EPUB inspection/extraction. The uploader validates PDF signature, UTF-8 TXT and DOCX/EPUB archive structure/limits. Current README and ADR describe Qdrant as infrastructure/planned retrieval, not completed semantic search.

Current settings use PostgreSQL when `DB_NAME` is configured and otherwise fall back to SQLite. DRF defaults to authenticated access. A custom middleware separates `/admin/` and researcher sessions using `mizan_admin_sessionid` and `mizan_researcher_sessionid`. The current ADR records local-only Ollama at `127.0.0.1:11434`.

**Evidence boundary:** findings above come from the uploaded ZIP source snapshot and its README/Phase 0 ADR. This is not a live database introspection, production security audit, or runtime health test.

## 4. Domain-driven application structure

### 4.1 Target domain map

| Domain | Owns | Must not own |
|---|---|---|
| `accounts` | User profile extension, roles, grants, research groups | Scholarly truth or source records |
| `catalog` | Persons/authors, works, contributor roles, publishers, editions, volumes | Extracted text and OCR runtime |
| `sources` | Source records, acquisition, rights, verification events, source manifests | Research interpretations |
| `library` (existing; evolves) | Documents, file references, content units, ingestion lifecycle | Hadith grading or fiqh verdict logic |
| `corpus` | Text versions, blocks, passages, alignment and textual review | Bibliographic identity |
| `citations` | Citation identities and exact locators | Claim verification itself |
| `research_core` | Research entities, aliases, identifiers, relationships, scholarly assertions and evidence | Domain-specific payloads where a typed model is needed |
| `quran` | Surah/ayah identities, text witnesses/variants, tafsir links, revelation assessments | General book catalog |
| `hadith` | Hadith records, matn variants, isnad routes, narrators, grading assessments | Generic source rights |
| `fiqh` | Madhhabs, questions, opinions, rulings, usul principles | General assertion/evidence infrastructure |
| `aqidah` | Doctrine topics/positions and their scholarly attribution | General identity/citation infrastructure |
| `tasawwuf` | Traditions, tariqas, lineages, concepts and attributed teachings | General person/source records |
| `history` | Events, participants, places, uncertain dates and chronologies | Generic entity identity |
| `linguistics` | Arabic roots, lexical entries/forms, morphology and grammar analyses | Corpus source storage |
| `manuscripts` | Manuscript witnesses, folios, readings and collation | General document upload lifecycle |
| `search` | Lexical index state, embedding metadata, retrieval orchestration | Canonical source text |
| `ai_runtime` (existing) | Provider adapters, model calls, prompt execution boundary | Scholarly authority or truth decisions |
| `workflows` | Processing jobs, attempts, leases, outbox and worker events | Domain-specific scholarly data |
| `governance` | Audit events, policy records, retention and provenance controls | Duplicate copies of domain records |

### 4.2 App creation policy

Do not create every future app now. Keep current `library` and `ai_runtime` operational. Create a domain app when its phase begins and its entities/service contracts are sufficiently specified. Avoid circular imports: domain apps depend on shared catalog/sources/corpus/citations/research_core interfaces, not on one another's internal models. Use service functions and explicit selectors; avoid putting complex scholarly logic in Django model `save()` methods.

### 4.3 Dependency direction

`accounts/governance` are cross-cutting. `catalog` and `sources` are upstream of `library/corpus`. `citations` depends on catalog/library/corpus. `research_core` depends on identities and citations. Specialized domains depend on shared research/citation infrastructure. `search` indexes governed passages and entities. `ai_runtime` consumes retrieval services and returns execution outputs; it does not write verified scholarly records. `workflows` orchestrates idempotent work across domains.

## 5. Core database architecture

PostgreSQL is the system of record. Use normal relational tables and explicit FKs for durable entities. Use JSONB only for genuinely variable engine output, source metadata extensions or domain-specific structured payloads that are not yet stable; do not hide core relations in JSON.

### 5.1 Primary key and naming policy

- Existing BigAutoField IDs remain unchanged during the first evolution; existing Document UUID remains unchanged.
- New cross-domain records may use UUID primary keys where external references, import/export or stable distributed identifiers are valuable. Do not force a disruptive all-table UUID conversion.
- Use singular model names and snake_case DB columns. Foreign keys use `<name>_id`.
- Store timestamps as `timestamptz` through Django timezone-aware DateTimeField; use UTC in storage and render in user locale.
- Use `date` only for a genuinely date-only value. Historical/uncertain dates use structured date assertion fields, not fabricated exact dates.
- Use `DecimalField` only for numeric values requiring decimal precision; do not use floats for coordinates or scores that require exact audit.
- Avoid physical table renames purely for terminology. `Book` may remain the physical model while its domain meaning is documented as Work until a safe API/data migration is justified.

### 5.2 Common lifecycle fields

For mutable business entities: `created_at timestamptz NOT NULL`, `updated_at timestamptz NOT NULL`, optional `created_by_id` and `updated_by_id` to AUTH_USER_MODEL with SET_NULL. Append-only events have `created_at`, actor, reason and correlation ID, but no routine update/delete endpoint. Avoid adding these fields blindly to pure join tables or immutable version records.

### 5.3 Referential integrity and deletion

- Use PROTECT for bibliographic/source records with scholarly citations or audit history.
- Use CASCADE only for dependent technical children that have no independent scholarly identity (e.g. text blocks under a version), and only after retention policy is clear.
- Use RESTRICT/PROTECT for records that are cited, verified or part of audit history.
- Prefer soft-retirement (`status='retired'`, `retired_at`, `retired_by`) for works, people, entities, taxonomy terms and domain records once referenced.
- File asset deletion is a governed storage operation; deleting a DB row must not silently orphan or erase original bytes.
- Cross-parent invariants that cannot be expressed as ordinary FKs must be validated in a transaction/service and tested (e.g. a Document's Volume must belong to its Edition and Work).

## 6. Research entity architecture

A generic `ResearchEntity` provides canonical identity across domains. Minimum fields: `id`, `entity_type`, `canonical_label`, `canonical_label_ar`, `description`, `status`, `created_at`, `updated_at`. Related tables:

- `EntityAlias(entity_id, alias_text, language, script, alias_type, is_preferred, source_citation_id)`.
- `EntityIdentifier(entity_id, scheme, identifier_value, source_citation_id)` with unique `(scheme, identifier_value)` when globally unique.
- `EntityRelationship(subject_entity_id, predicate, object_entity_id, provenance_type, status, valid_from, valid_to, asserted_by_id, citation_id, notes)`.
- `ScholarlyAssertion(subject_entity_id, predicate, object_entity_id nullable, object_literal JSONB nullable, domain, epistemic_status, attribution_person_id nullable, source_citation_id nullable, context, valid_time, notes)`.
- `AssertionEvidence(assertion_id, citation_id, evidence_role [supports/opposes/qualifies/mentions], notes)`.
- `AssertionAssessment(assertion_id, assessor_id, assessment_status, rationale, created_at)`.

`entity_type` is controlled vocabulary, not free-form UI text. Examples: person, work, place, institution, concept, manuscript, event, narrator, madhhab, tariqa, Quran passage, hadith record. Specialized tables may use a one-to-one FK to ResearchEntity for domain-specific attributes. Never use one generic JSON blob to model isnad order, legal opinions or manuscript variants.

Epistemic status must distinguish at least: reported, attributed, accepted_by_named_authority, disputed, rejected_by_named_authority, inferred, uncertain, unknown. These are not universal truth values; the named assessor/scholar, source and context are stored.

## 7. Source, bibliography and citation architecture

### 7.1 Work → Edition → Volume

- `Work` is the abstract intellectual work.
- `WorkContributor` links a Person to a Work with `role_code`, sequence, attribution text and certainty. Roles include author, compiler, editor, translator, commentator, verifier, editor-of-critical-edition and other controlled values.
- `Edition` is a publication manifestation of a Work and carries publisher, edition statement, publication year/date, place, ISBN/other identifiers, language and notes.
- `Volume` belongs to one Edition and has a unique `(edition_id, volume_number)`. Volume numbering and printed pagination are edition-specific.
- Publisher is a separate record. Publisher name variants and locations should not be conflated with an edition's imprint statement.
- Preserve original bibliographic strings and normalized values separately when a date/name is uncertain.

### 7.2 Source and acquisition

`SourceRecord` represents the supplying repository, publisher, institution, website, collection, dataset or private collection. `SourceAcquisition` records how a specific asset/document was obtained: acquisition method, acquired_at, acquired_by, donor/supplier, source URL or accession, transaction/permission reference, acquisition notes, evidence attachment and chain-of-custody notes. Do not put acquisition facts only in a free-text Document note.

`SourceRights` (or a versioned rights record) stores rights holder, rights status, license name/URL/version, permitted uses, restrictions, required attribution, territory, validity dates and evidence/citation. Rights status and scholarly authenticity/verification are independent dimensions.

`SourceVerificationEvent` is append-only and records previous/new state, actor, rationale and timestamp. Current state on SourceRecord is a projection/cache; the event history is authoritative. Admin must not permit direct edits that bypass the transition service.

### 7.3 Source metadata contract

For every Document/SourceManifest, capture or explicitly mark unknown/not-applicable:

1. Original source/source institution and external identifier.
2. Author/contributor identity and role (including unknown/attributed/anonymous status).
3. Title and original-language title.
4. Publisher/imprint or manuscript collection.
5. Edition/printing/recension.
6. Publication year/date with uncertainty/era.
7. Volume/part.
8. Page numbering system (printed Arabic/Indic/Roman/folio/unpaginated; PDF page index kept separately).
9. Language(s), script and direction.
10. Source format and media type.
11. Rights/licence and permitted use.
12. Acquisition method, date, actor, supplier and evidence.
13. File checksum, byte size, storage identity and original filename.
14. Processing history, software/engine/model versions, timestamps, outcome and warnings.
15. Verification/review status and responsible actor.

Missing data must be represented as `unknown`, `not_applicable`, `not_checked` or `disputed` as appropriate, never guessed. Completeness is measured by field status, not by forcing fake values.

### 7.4 Citation architecture

`Citation` is a reusable reference identity; `CitationLocator` carries one or more exact locations. Locator fields include document/edition/volume, printed_page_start/end (text to preserve non-numeric folios), pdf_page_index (zero-based), pdf_page_number (one-based), folio/side, chapter/section, paragraph/block, line, passage_id, text_version_id, start_offset/end_offset and locator_note. Only relevant dimensions are populated. Printed pagination is never inferred from PDF page number.

A citation may refer to a source passage or a bibliographic location without OCR. When text exists, a version-bound Passage locator is preferred. Passage must belong to exactly one TextVersion. Text changes create a new TextVersion and passage set or an explicit verified mapping; old citations continue to resolve to the old version.

## 8. Corpus, file and text architecture

### 8.1 FileAsset and storage

`FileAsset` fields: UUID, sha256, byte_size, media_type, original_filename, storage_backend, storage_key, asset_role (original_scan, born_digital_original, page_image, OCR_derivative, thumbnail, export, attachment), created_at, uploaded_by, retention_state, rights_record_id. SHA-256 and byte size identify bytes; identical bytes may be deduplicated physically but must not collapse distinct Document/source identities.

Use private storage outside public static serving. Local filesystem is acceptable for the current single-machine development stage behind a storage adapter. The adapter contract should support `save`, `open/read`, `exists`, `delete` (governed only), `checksum`, `stat`, and signed/private download authorization. Keep originals, derivatives and temporary/quarantine files in separate logical roots. Never trust uploaded filename as a storage path. Validate MIME/signature, size, archive expansion limits, path traversal, malware policy and format parser limits. Quarantine before processing when deployment exposure requires it.

### 8.2 Text lifecycle

`ContentUnit` generalizes Page: PDF page, image page, EPUB section, DOCX document/section, TXT segment, manuscript folio. Fields include document_id, unit_type, sequence/index, source_unit_label, physical dimensions/rotation, printed page label, is_current and metadata.

`TextVersion` belongs to ContentUnit and records version_number, representation_type, language, script, direction, source_method, engine/provider/version, parent_version_id, text, checksum, quality JSONB, created_at, created_by. Representation types: raw_extraction, OCR_raw, corrected_transcription, normalized_search, transliteration, translation, editorial_text. A representation is never silently overwritten by another.

`TextBlock` stores structural segmentation (heading, paragraph, footnote, table, marginalia, heading, other) and geometry. `Passage` stores a version-bound retrievable/citable segment, sequence, structural locator, offsets and checksum. Review decisions point to exact versions and create a new corrected TextVersion when text changes. Textual approval is not source verification or scholarly approval.

## 9. User, permission and research access architecture

Keep Django AUTH_USER_MODEL as the identity provider. Do not create a parallel user table. Add `UserProfile` only for non-auth profile fields. Use composable roles:

- Owner: full project authority.
- Administrator: account/configuration and delegated operational administration.
- Researcher: create research drafts and use permitted corpus.
- Text Reviewer: assigned transcription review.
- Source Verifier: source provenance/rights verification.
- Scholar/Domain Assessor: attributed domain assessments within declared authority/scope.
- Read-only: view permitted records.

Core tables: `Role`, `Permission`, `RolePermission`, `UserRoleAssignment`, `ResearchGroup`, `GroupMembership`, `ObjectGrant` (optional scoped grant), `AccessAuditEvent`. Role assignments include granted_by, granted_at, valid_from/to, scope type/id and revocation. A role is not proof of religious/scholarly qualification; credentials and declared scope are separately documented and auditable.

Permission checks are server-side at view, API, service and object scope. Frontend hiding is not security. Use deny-by-default. Separate admin/researcher session cookies currently exist; preserve this behavior, but test CSRF, cookie Secure/HttpOnly/SameSite, logout isolation, session fixation and staff/nonstaff boundaries. BasicAuthentication must not be enabled over non-TLS production traffic. Production requires DEBUG=False, HTTPS, secure cookies, restricted ALLOWED_HOSTS, private media delivery, upload throttling, secrets outside source control and backup/restore tests.

## 10. Search infrastructure

### 10.1 Search tiers

1. PostgreSQL lexical search for authoritative metadata and content.
2. `pg_trgm` for fuzzy title/name matching and spelling variants.
3. Language-aware normalization/tokenization for Arabic, Urdu, Persian, Ottoman Turkish, Hindi and English; store normalized text separately from source display text.
4. Qdrant for semantic vectors only after the embedding model and multilingual evaluation are approved.
5. Hybrid retrieval combines lexical and semantic candidates; reranking is a distinct evaluated stage.

### 10.2 Search records and lifecycle

`SearchableContent`/index projection references object type/id, source TextVersion/Passage, language, normalized text, metadata and updated_at. `EmbeddingModel` records provider/model/version/dimension/normalization configuration. `EmbeddingRecord` records passage_id, text_version_id, model id, collection, vector_point_id, content_hash, status and indexed_at. Qdrant payload includes stable DB IDs, language, work/edition, domain, rights/access visibility and version. Do not put confidential text in public payloads.

On text change, enqueue idempotent reindex for the new version and mark old vector as superseded; never silently overwrite citation identity. On deletion/rights revocation, enforce access filter and delete/rebuild derived vectors according to policy. Rebuild is from PostgreSQL + governed file/text source. Search result always returns citation locator and version.

## 11. AI service architecture

`ai_runtime` remains the provider boundary. Define interfaces: `health()`, `list_models()`, `generate(messages, model_config, timeout)`, `embed(texts, model_config)`, optional `rerank(query, candidates)`. Ollama adapter is current local provider. Do not allow domain code to call Ollama HTTP directly.

`ModelRegistry` stores provider, model name, version/tag, task type, context limit, embedding dimensions, language support, local/remote classification, approval status and evaluation profile. `PromptTemplateVersion` stores template name/version, purpose, language, author and checksum. `AIExecution` records model/prompt/config versions, request/response hashes, timestamps, token/latency metrics, status and error class. `ResearchRun` and `RetrievalItem` preserve query and exact evidence retrieved. `GeneratedAnswer`/`AnswerClaim`/`AnswerCitation` connect answer spans/claims to citations.

Answer policy:
- Retrieve before answering when the task requires platform corpus evidence.
- Distinguish direct quotation, paraphrase, attributed scholarly view, inference, uncertainty and no-evidence response.
- Never fabricate page numbers, isnad links, hadith grades or scholarly consensus.
- A citation must resolve to exact edition/location/version.
- AI outputs are drafts/research assistance, never automatically verified scholarly assertions.
- Keep prompt injection from source documents isolated as untrusted content; source text cannot instruct tools or alter system policy.
- Log enough provenance to reproduce a run while applying data minimization and access controls.

## 12. Knowledge graph

Use PostgreSQL relational graph tables initially: ResearchEntity, EntityAlias, EntityIdentifier, EntityRelationship, ScholarlyAssertion, AssertionEvidence and AssertionAssessment. Edges are typed, directed, sourced, attributable, time-aware and status-aware. Support documented, attributed, disputed, inferred and uncertain relations. Avoid treating an inferred edge as fact.

Graph queries should be built on indexed FK/predicate/entity columns and recursive CTEs for bounded traversals. Add graph materialized views only after query profiling. Neo4j or another graph database is deferred until PostgreSQL graph traversal is demonstrably inadequate and a sync/reconciliation strategy is funded.

## 13. Task processing architecture

Keep the database-backed queue initially. Target job fields: id, job_type, target_type/id, status, priority, idempotency_key, input_version, attempt_count, max_attempts, worker_id, claimed_at, heartbeat_at, lease_expires_at, progress_current/total, result JSONB, error_code/message, created_at, started_at, finished_at. `ProcessingAttempt` stores each attempt and error; `TaskEvent` records transitions.

Lifecycle: queued → claimed/running → completed | partial | failed | cancelled. Retry only transient failures; permanent validation errors fail immediately. Use atomic `select_for_update(skip_locked=True)` claim, idempotency key, lease heartbeat and bounded retry/backoff. A stale worker is reclaimed only after lease expiry, not a fixed `started_at` age. Document the current 30-minute threshold as legacy behavior until heartbeat is implemented. Long OCR jobs must not be reclaimed while alive. External queue (Celery/Redis) is deferred pending measured throughput/concurrency need.

Use transactional outbox for DB changes that must trigger indexing/embedding so a committed text version cannot be lost between database commit and enqueue. Consumers are idempotent.

## 14. Audit and provenance

`AuditEvent` fields: id, actor_id nullable, action, object_type, object_id, before_summary JSONB, after_summary JSONB, reason, request_id/correlation_id, source_ip (policy-controlled), user_agent (policy-controlled), created_at. Redact secrets, credentials and unnecessary personal data. Do not store full uploaded source content in audit rows.

Separate event families:
- SourceAcquisitionEvent: how/when/from whom obtained.
- SourceVerificationEvent: authenticity/provenance decision.
- RightsDecisionEvent: legal/licence decision.
- ProcessingAttempt/TaskEvent: machine processing history.
- ReviewDecision: textual review.
- ScholarlyAssessment: scholarly judgement/grade/opinion.
- AuditEvent: user/system action history.

Append-only means normal application roles cannot update/delete historic events. Corrections are new events with supersedes/reverses reference. PostgreSQL privileges and service-layer controls should reinforce this. Do not claim tamper-proof immutability against DB superusers; backups and external audit export are operational controls.

## 15. Full-scope research domain extension architecture

Shared identity, source, corpus, citation, assertion and audit models are reused. Domain tables are typed and linked; no subject domain stores source provenance in a separate incompatible scheme.

| Domain | Foundational specialized tables / structures |
|---|---|
| Quran | `Surah`, `Ayah`, `QuranTextWitness`, `QuranTextVersion`, `Qiraat`, `QiraatVariant`, `TafsirWorkLink`, `TafsirPassageLink`, `AsbabAlNuzulReport`, `RevelationAssessment`, `MakkiMadaniAssessment`. Revelation chronology/classification is an attributed assessment, not a single hardcoded truth field. |
| Tafsir | Tafsir passages remain Corpus `Passage` records linked through `TafsirPassageLink` to ayah/range, Tafsir work/edition, scholar attribution, interpretation topic and citations. Multiple tafsir views coexist. |
| Hadith | `HadithCollection`, `HadithRecord`, `MatnVariant`, `IsnadRoute`, `IsnadLink` (ordered narrator link), `NarratorProfile`, `NarratorNameVariant`, `NarratorAssessment`, `JarhTadilAssessment`, `HadithGradeAssessment`, `HadithTopicLink`. Each grade is attributed to a named scholar/source and date/context. |
| Fiqh / Madhhabs / Usul | `Madhhab`, `FiqhQuestion`, `FiqhOpinion`, `FiqhRuling`, `FiqhEvidenceLink`, `UsulPrinciple`, `LegalMethod`, `ComparativePosition`. Opinions are attributed and source-backed; disagreement is first-class. |
| Aqidah | `DoctrineTopic`, `DoctrinePosition`, `SchoolAttribution` and shared ScholarlyAssertion/Evidence. Distinct attributed positions are retained; no forced single global verdict. |
| Tasawwuf | `SpiritualTradition`, `Tariqa`, `Lineage`, `LineageLink`, `TasawwufConcept`, `Practice/Adab` and attributed teaching/evidence. Lineage links carry source, attribution, uncertainty and time. |
| Seerah / History | `HistoricalEvent`, `EventDateAssessment`, `EventParticipant`, `EventPlace`, `ChronologyAssertion`; date uncertainty and source-specific disagreement are preserved. |
| Arabic Linguistics | `ArabicRoot`, `LexicalEntry`, `LexicalForm`, `MorphologicalAnalysis`, `GrammarAnalysis`, `SemanticRelation`, `UsageAttestation`; each analysis links to text passage and scholarly attribution. |
| Manuscripts | `ManuscriptWitness`, `ManuscriptDescription`, `ManuscriptFolio`, `ManuscriptReading`, `VariantReading`, `CollationRecord`, `WitnessRelationship`; folio/recto/verso and variant readings link to exact images/passages and citations. |
| Knowledge graph | All above may be ResearchEntity types and/or specialized records; typed relationship and assertion provenance remains common. |

## 16. Metadata completeness and governance workflow

At acquisition, create SourceRecord + SourceAcquisition + FileAsset + Document manifest. Record metadata values with status: `known`, `unknown`, `not_applicable`, `not_checked`, `disputed`. A required metadata checklist must never force a fabricated value.

Recommended workflow:
1. Acquired → quarantined/rights pending.
2. File validated → checksum and file metadata captured.
3. Bibliographic metadata linked → missing fields explicitly marked.
4. Rights decision recorded.
5. Source provenance verification recorded.
6. Ingestion job created with pipeline version.
7. Raw extraction/OCR stored as immutable TextVersion.
8. Textual review performed and correction creates new version.
9. Passage segmentation and search indexes derived.
10. Citation and scholarly research may reference the exact version.
11. Reprocessing creates a new processing run/version; never destroys history.

A document may be searchable while text is unreviewed, but UI/API must visibly distinguish machine-extracted from human-reviewed. Rights-restricted material must be filtered from unauthorized retrieval and AI context.

## 17. Migration and rollout strategy

No schema migration is authorized by this architecture package. When implementation is approved:
1. Freeze schema baseline and export current schema/data counts.
2. Add new tables/nullable FKs first; no destructive rename/drop.
3. Backfill Work/Person/ContributorRole from Book/Author; preserve original IDs and text.
4. Add FileAsset rows around existing Document.file; calculate/verify hashes and preserve storage keys.
5. Map Page to ContentUnit and ExtractionVersion to TextVersion with source/version/checksum retained.
6. Keep compatibility projections/API serializers while both old and new paths are tested.
7. Add Citation/Passage and research core only after corpus version semantics are stable.
8. Add domain modules in roadmap order, using shared evidence/citation.
9. Dual-read/compare, then switch consumers; only later deprecate duplicated fields.
10. Destructive cleanup requires backup, row-level reconciliation, rollback plan and explicit owner approval.

Do not parse free-text `Edition.editor` or `translator` into Person records automatically unless unambiguous. Preserve original text in migration notes and mark uncertain mappings for human reconciliation.

## 18. Phase 1 exit-criteria checklist

| Exit criterion | Design coverage | Status |
|---|---|---|
| Domain-driven application structure | Section 4 | Defined |
| Core database architecture | Sections 5 and 17 | Defined |
| Research entity architecture | Section 6 | Defined |
| Source and citation architecture | Section 7 | Defined |
| Book and edition relationships | Section 7.1 | Defined |
| User and permission architecture | Section 9 | Defined |
| File storage architecture | Section 8.1 | Defined |
| Search infrastructure architecture | Section 10 | Defined |
| AI service architecture | Section 11 | Defined |
| Knowledge graph architecture | Section 12 | Defined |
| Task processing architecture | Section 13 | Defined |
| Audit and provenance architecture | Section 14 | Defined |
| Required source metadata | Sections 7.3 and 16 | Defined |
| Entire final research scope | Section 15 | Defined |
| No avoidable foundational redesign | Shared identity/citation/evidence/text version contracts across domains | Design criterion addressed |

**Phase 1 design package is complete as a documented baseline.** Before any implementation, the project owner should review and sign off the baseline. That sign-off is not an invitation to reopen settled decisions without evidence; changes must be logged as ADR amendments.
