# 11 — End-to-End Workflow Contracts
**Status: target design; no runtime workflow implemented by this document**

## Workflow A — Source acquisition and registration
1. Curator identifies source and records bibliographic identity, origin, acquisition channel/date and evidence.
2. SourceRecord is created/resolved independently from the bytes.
3. Acquisition event records who obtained which copy, from where, when and under what terms.
4. Rights reviewer records license/permission/terms, jurisdiction if relevant, allowed uses, restrictions, evidence and review date.
5. Verification event assesses authenticity/completeness/provenance separately from rights status.
6. Document record links to Work/Edition/Volume and the acquired witness/copy.
7. FileAsset records immutable bytes, checksum, size, storage identity and integrity state.
8. Access policy is computed before indexing, preview, OCR, AI context or export.

**Failure handling:** missing rights evidence → restricted/pending; checksum mismatch → quarantine; uncertain bibliographic identity → unresolved candidate, not guessed merge.

## Workflow B — Ingestion and OCR
1. Authorized user submits a Document for processing.
2. Validate extension, MIME/signature, archive structure, size, page count and malware/quarantine policy.
3. Create IngestionRun and idempotent WorkflowJob with input asset checksum and pipeline version.
4. Worker claims job under a lease; emits heartbeat and JobAttempt.
5. Inspect file and create ContentUnits (PDF pages initially; other formats use format-specific units).
6. Extract embedded text and/or OCR; preserve engine/model/version, parameters, language/script, confidence/quality and raw output.
7. Create immutable TextVersion; do not overwrite earlier extraction.
8. Segment TextBlocks/Passages against that exact version.
9. Emit completion/failure event; retry only transient/idempotent stages.
10. Place low-confidence or structurally suspicious pages into human review queue.

## Workflow C — Textual review and correction
1. Reviewer opens a version with source image/page context and exact offsets.
2. Reviewer records correction proposal and rationale.
3. Accepted correction creates a new TextVersion linked to prior version; prior version remains immutable.
4. ReviewDecision references the exact version reviewed, reviewer, decision, timestamp and rationale.
5. If correction changes offsets/segmentation, create new TextBlocks/Passages; preserve old passage identities and supersession links.
6. Review status never means source authenticity, hadith grading or scholarly correctness.

## Workflow D — Scholarly research assertion
1. Researcher creates/resolves canonical ResearchEntity and aliases.
2. Researcher records an attributed assertion with subject, predicate, object/value, domain, scope, time validity and epistemic status.
3. AssertionEvidence links one or more citations and exact CitationLocators.
4. Assessment records scholar, method, madhhab/tradition where relevant, conclusion, rationale and timestamp.
5. Conflicting assessments coexist; no silent overwrite or false consensus.
6. AI may suggest candidates/evidence but cannot approve, grade or authenticate an assertion.

## Workflow E — Citation and retrieval
1. User query is authorized against workspace, collection, source rights and domain scope.
2. Lexical retrieval queries PostgreSQL; semantic retrieval queries only eligible, version-bound vector projections.
3. Results are fused/reranked; each result retains Document, ContentUnit, TextVersion, Passage and locator identity.
4. Citation rendering distinguishes printed page, PDF page/index, folio, chapter/section, hadith number, Quran surah/ayah and line/offset.
5. A cited answer stores a ResearchRun with query, filters, retrieval version, prompt/model/provider, selected evidence and generated response.
6. If evidence is missing, system reports insufficient evidence rather than inventing a locator.

## Workflow F — AI-assisted answer
1. User submits question; permission filter runs before retrieval.
2. Retrieval returns eligible evidence with exact version and locator.
3. AI adapter receives bounded context and explicit instruction to distinguish source quotation, paraphrase, inference and uncertainty.
4. AIExecutionTrace records model/provider/version, prompt template version, parameters, timestamp, token/latency metadata and evidence IDs (not secret credentials).
5. Output is labelled AI-generated/unverified until human assessment.
6. Every factual scholarly claim intended for research use must be traceable to evidence; unsupported claims are marked or withheld.
7. No autonomous rights changes, textual approvals, hadith grading or scholarly verification.

## Workflow G — Rights revocation / source restriction
1. Rights reviewer records new decision with evidence and effective time.
2. Access policy immediately blocks source bytes and derived access where required.
3. Search and vector projections are tombstoned/filtered; caches and exports are addressed per policy.
4. Existing citations remain as bibliographic records but access to restricted content is denied.
5. Audit trail records decision, affected assets, derived indexes and completion status.

## Workflow H — Background job recovery
1. Job is enqueued with idempotency key, payload schema/version and retry policy.
2. Worker claims atomically and creates attempt/lease expiry.
3. Heartbeat extends lease; expired lease permits safe reclaim.
4. Completion writes result and outbox event atomically where possible.
5. Consumer deduplicates by event ID/idempotency key.
6. Permanent failures go to dead-letter/manual review; transient failures retry with bounded backoff.
7. Stale-job age based only on `started_at` is insufficient for long-running OCR; heartbeat is required in target design.
