# Mizan Al-Tahqiq — Phase 1 P0 Architecture Contracts

**Version:** 0.1 — proposed design decisions  
**Status:** Working proposal; owner approval required before Phase 1 closure  
**Basis:** Phase 1 Architecture Baseline 1.0, Reconciliation Audit 0.1, and source snapshot `Mizan-Al-Tahqiq_SAFE_AUDIT_20261127_121650.zip`  
**Implementation:** None. No model, migration, database, settings, or runtime changes.

## Purpose

Resolve the six P0 blockers identified by the reconciliation audit. These are target architecture contracts, not implementation instructions. The current `library` app and existing rows remain the compatibility baseline.

---

## P0-01 — Canonical text lifecycle

### Existing state
- `Page` represents a document unit and stores `extracted_text`.
- `ExtractionVersion` stores versioned text per page, source (`embedded`, `ocr`, `manual`), engine metadata, hash and quality.
- `TextBlock` belongs to an `ExtractionVersion`.
- `ReviewRecord` points to an extraction and can store `reviewed_text`.

### Proposed contract
1. Preserve `Page` as the current physical model/table during the compatibility period; treat its domain role as a `ContentUnit` (initially PDF page).
2. `ExtractionVersion` is the legacy/current implementation of a versioned text artifact. The future canonical `TextVersion` must retain provenance: source method, engine/model and version, creation actor, timestamp, checksum, language/script/direction, and verification state.
3. Do not overwrite prior text versions. OCR, re-OCR, manual correction, normalization, transliteration and translation each create a new immutable version with an explicit `version_kind` / derivation relationship.
4. `TextBlock` remains tied to one exact text version. Blocks carry stable order plus character offsets and optional page geometry. Offsets are version-specific.
5. `Passage` is a stable citation/search segment tied to an exact `TextVersion`; it is not assumed to survive resegmentation. A new segmentation creates new passage identities and preserves supersession/derivation links.
6. `Page.extracted_text` is treated as a compatibility projection of the current selected extraction, not an independent source of truth. During transition, reads must define which extraction is current; never silently overwrite history.
7. A textual review decision references the exact version reviewed. A correction creates a new version; the review record itself stores decision, reviewer, rationale and timestamps, not the corrected canonical text.

### Acceptance conditions
- Every searchable/citable text can be traced to a source document, content unit and exact immutable version.
- A citation to an old version remains resolvable after OCR correction or resegmentation.
- Machine extraction is never represented as scholarly verification.

---

## P0-02 — File identity and storage

### Existing state
`Document` owns a Django `FileField`, original filename, SHA-256, size and format. Upload path is derived from the Document UUID. The ingestion workflow reads the file from this field.

### Proposed contract
1. Introduce `FileAsset` as the identity of stored bytes and storage metadata; `Document` remains the bibliographic/contextual record that describes a digital witness/copy.
2. Initial cardinality: one `Document` references exactly one primary original `FileAsset`; one `FileAsset` may be referenced by multiple Documents only when they intentionally describe the same exact byte object. Do not infer that identical bytes mean identical edition or source provenance.
3. Keep checksum and byte size on `FileAsset`; use `(algorithm, digest, size)` for byte identity. Do not globally enforce a uniqueness rule that prevents multiple provenance/acquisition records or bibliographic records from referring to identical bytes. Deduplication is a storage optimization, not a scholarly identity merge.
4. Store storage backend, private storage key/path, original filename, MIME/format, byte size, checksum, created time and integrity/availability state. Never expose private storage keys as public URLs.
5. Migration is additive: create FileAsset rows pointing to existing file paths; do not move, rename or delete bytes in the first migration. Verify file existence and checksum before any later storage migration.
6. Keep `Document`'s current `file`, `sha256` and `file_size` as compatibility fields until all reads/writes use FileAsset and a tested rollback window has passed.
7. A source download/acquisition event is separate from the stored byte object. The same bytes acquired from two sources may have two acquisition records.

### Acceptance conditions
- Existing media paths remain readable during transition.
- File deduplication never collapses distinct source provenance.
- Storage can later move between local/private object storage without changing scholarly document identity.

---

## P0-03 — Bibliographic identity and contributors

### Existing state
`Author` has name, Arabic name, biography and string birth/death years. `Book.authors` is a many-to-many relation. `Edition.editor` and `Edition.translator` are free text. Existing IDs are BigAutoField.

### Proposed contract
1. Introduce a canonical `Person` identity for a real or historically attested individual; preserve existing `Author` records and primary keys during transition.
2. Map each existing Author to one Person using an explicit one-to-one identity mapping initially. Do not merge records solely because names look similar; ambiguous identity remains unresolved pending evidence.
3. Replace the conceptual meaning of `Book.authors` with an explicit `WorkContributor` relation containing `person`, `role`, `display_order`, attribution certainty/status, optional contribution note and supporting citation/source.
4. Contributor roles include author, compiler, editor, translator, commentator, verifier and other extensible roles. Role is per Work or Edition as appropriate; editor/translator of an edition must not be incorrectly attached as author of the underlying Work.
5. Support anonymous, collective, pseudonymous and uncertain attribution without inventing a Person. Model an attribution statement separately from a confirmed identity when necessary.
6. Preserve original-script, transliterated and alternate names as name records with language/script and preferred-name designation. Names are not separate people.
7. Keep birth/death year strings source-faithful in the initial mapping. Normalize dates only when source precision supports it; allow AH/CE, ranges, circa and unknown values without false precision.
8. Do not change existing Book/Author table names or PK types in the initial architecture implementation.

### Acceptance conditions
- One person can have multiple roles across works and editions.
- The same person can be represented in Arabic, Urdu, Persian, transliteration and other name forms without duplicate identities.
- Uncertain attribution remains explicit and evidence-linked.

---

## P0-04 — Source governance split

### Existing state
`SourceRecord` currently combines source identity, source type, URL, license fields, rights status, verification status, access date and verifier. `SourceVerificationEvent` stores both verification and rights before/after statuses.

### Proposed contract
Separate four concepts:

1. **SourceRecord** — identity of a repository, publisher, institution, website, archive, dataset or private collection. It describes where material originates or is hosted.
2. **SourceAcquisition** — a specific acquisition event for a particular source item/asset: source record, source item identifier/URL, acquisition method, acquired/accessed timestamp, actor/process, acquisition notes, checksum observed, and chain-of-custody details where available.
3. **RightsRecord** — rights/license assessment for a particular item or defined collection and intended use. Store rights holder/claimant, license/terms, evidence URL/document, scope, permitted uses, restrictions, attribution requirement, assessment status, assessor and dates.
4. **Independent event histories** — source verification events record provenance/reliability checks; rights decision events record legal/permission assessment changes. Neither status overwrites the other.

Rules:
- Unknown rights means “not cleared for the intended use”; it is not permission.
- Verified provenance does not imply permission to reproduce; public-domain/permission status does not imply scholarly reliability.
- A source may have multiple acquisitions and multiple rights assessments over time or for different uses.
- `Document` may link to a SourceRecord for compatibility, but its exact source item/acquisition relationship should be explicit in the target model.
- Existing combined SourceVerificationEvent rows are retained as historical evidence and mapped into the appropriate event streams only where the prior field values support that mapping. Do not fabricate missing event types.

### Acceptance conditions
- Provenance verification, legal rights and content review are independent state dimensions.
- Every imported asset can be traced to an acquisition/source record.
- Intended use (private research, internal indexing, quotation, public display, redistribution) is assessed explicitly.

---

## P0-05 — Citation locator contract

### Proposed contract
A Citation identifies a claim/reference to a specific scholarly object or passage. A CitationLocator identifies the exact location within a source version. A citation without a sufficiently precise locator is allowed only when the source itself has no finer stable locator, and must carry a locator precision value.

Each locator should support:
- target object: Document, ContentUnit, TextVersion, Passage or another cited scholarly entity;
- locator scheme/type: printed page, PDF page index, PDF page number, folio, section/chapter, hadith number, ayah/surah, line, paragraph, timestamp or other domain-specific locator;
- raw source locator label exactly as printed/presented;
- normalized locator components only when unambiguous;
- exact text version/passage reference where applicable;
- optional start/end offsets or range;
- locator notes and precision/confidence.

Rules:
1. Printed page number, PDF zero-based index and PDF one-based page number are distinct fields/schemes and must never be conflated.
2. Folio requires recto/verso where the source uses that convention.
3. Hadith numbering and Quranic surah/ayah references are domain locators, not generic page numbers.
4. A citation to OCR text must point to the exact OCR TextVersion; a later correction must not silently change the cited text.
5. A locator may carry both a human-readable label and structured components.
6. Validation is scheme-specific; do not force every locator into numeric page fields.

### Acceptance conditions
- Every citation resolves to an identifiable source and locator.
- The displayed locator preserves the source's own numbering system.
- Old citations remain stable across reprocessing and text correction.

---

## P0-06 — Document ancestry integrity

### Existing state
`Document.book` is required; `edition` and `volume` are optional independent foreign keys. The database model does not enforce that `edition.book == document.book` or `volume.edition == document.edition`.

### Proposed contract
1. The conceptual hierarchy is Work → Edition → Volume → Document, but not every document has all levels known.
2. If `Document.volume` is set, `Document.edition` must be set and equal to `volume.edition`.
3. If `Document.edition` is set, `Document.book` must equal `edition.book`.
4. If only Work is known, Document may reference Work with Edition/Volume null. If Edition is known but volume is not, Volume may be null.
5. Unknown or disputed ancestry is represented as unresolved metadata/attribution, not by selecting a plausible parent.
6. Enforce cross-table ancestry through model/service validation and, where practical, database constraints/triggers; a simple FK alone cannot enforce equality across related tables.
7. Legacy inconsistent records must be reported and quarantined for review; do not silently rewrite their bibliographic ancestry.
8. `on_delete=CASCADE` on core scholarly records requires explicit review. Future architecture should favor PROTECT/soft-retirement for canonical scholarly entities so deleting a Work cannot cascade-delete Documents and their research history. Any change is additive and separately approved.

### Acceptance conditions
- No new Document can be saved with contradictory Work/Edition/Volume ancestry.
- Legacy anomalies remain traceable until manually resolved.
- Deleting catalog entities cannot silently destroy source files, citations or research history.

---

## Cross-contract rules

- Existing BigAutoField primary keys and Document UUID remain unchanged.
- Historical migrations remain immutable.
- New target tables are introduced additively and only in the implementation phase authorized by the roadmap.
- No destructive field/table removal until data migration, parity checks, backup and rollback are approved.
- Search indexes, embeddings, Qdrant points and AI outputs are derived artifacts; canonical text, source provenance, citations and scholarly assessments remain in PostgreSQL.
- All scholarly claims require evidence links and explicit attribution; AI-generated text is never treated as source evidence by itself.

## Owner approval checklist

The following defaults are recommended for approval:

- [ ] Approve immutable TextVersion + version-bound Passage lifecycle.
- [ ] Approve FileAsset as byte identity, with Document as bibliographic witness/context; one primary asset per Document initially, shared asset allowed.
- [ ] Approve Person + role-bearing WorkContributor/EditionContributor; preserve existing Author IDs and uncertain attributions.
- [ ] Approve independent SourceRecord, SourceAcquisition, RightsRecord and separate event histories.
- [ ] Approve Citation + scheme-specific CitationLocator tied to exact text version where applicable.
- [ ] Approve Work → Edition → Volume → Document ancestry invariants and non-destructive legacy anomaly handling.

**Phase 1 status:** These contracts are drafted, not owner-approved. Phase 1 remains open until the six P0 decisions and remaining module-level design are approved.
