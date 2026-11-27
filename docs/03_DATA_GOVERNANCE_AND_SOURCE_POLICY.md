# Data Governance, Source Metadata and Provenance Policy

## 1. Governing principles
1. Source identity, file identity, bibliographic identity and scholarly interpretation are separate concepts.
2. Preserve source bytes and raw extracted text. Never silently replace either.
3. Every derived object records what it was derived from, by which process/version, when and by whom.
4. Distinguish unknown, not applicable, not checked and disputed.
5. Scholarly verification, legal rights, transcription review and processing success are independent states.
6. Preserve disagreement and attribution. Never manufacture consensus.
7. AI-generated text is not a source and is not a verified scholarly record.

## 2. Required source manifest

| Metadata | Owner / level | Required representation |
|---|---|---|
| Original source | SourceRecord + SourceAcquisition | institution/repository/collection/supplier, external ID, URL/accession |
| Author | WorkContributor → Person | role and attribution status; anonymous/unknown allowed |
| Title | Work + WorkTitle | original, canonical, alternate, transliterated; language/script |
| Publisher | Edition → Publisher | imprint text and normalized publisher identity |
| Edition | Edition | edition statement, printing/recension, identifiers |
| Publication year | Edition | original date string plus normalized range/calendar if reliable |
| Volume | Volume | number/title; unknown if absent |
| Page numbering | Document/ContentUnit/CitationLocator | printed page system and PDF page index kept separately |
| Language | Work/Edition/Document/TextVersion | BCP-47-like language code, script, direction; multilingual supported |
| Source format | FileAsset/Document | extension, media type, format signature and byte size |
| Rights/licence | RightsRecord | status, license, rights holder, permitted uses, restrictions, attribution |
| Acquisition | SourceAcquisition | method, date, actor, supplier, permission/accession evidence |
| Processing history | ProcessingJob/Attempt/TextVersion | pipeline, engine/model version, start/end, result, warnings, checksums |

For each field store value and a field-state code where missingness matters: `known`, `unknown`, `not_applicable`, `not_checked`, `disputed`. Avoid storing literal text "N/A" in every data field.

## 3. State machines

### Source verification
`unverified → verified | disputed | rejected`; a later reassessment creates a new event and may supersede the prior state. Rejected means this source record/provenance claim was rejected, not necessarily that the work itself is false.

### Rights
`unknown → public_domain | open_license | permission_required | restricted | proprietary | disputed | expired`. Rights can change independently of source verification.

### Text processing
`uploaded → inspected → queued → processing → completed | partial | failed`. This is operational status only.

### Text review
`unreviewed → pending_review → approved | corrected | rejected`. Corrected creates a new TextVersion. ReviewRecord/ReviewDecision is not the text itself.

### Scholarly assessment
`unassessed → attributed_assessment`; outcomes are domain-specific and may conflict. No universal verified flag for all Islamic scholarship.

## 4. Acquisition and chain of custody
For each acquired item record:
- source and supplier identity;
- acquisition method (download, donation, scan, purchase, institutional transfer, user upload, other);
- acquisition timestamp and actor;
- accession/order/permission reference;
- source URL or collection shelfmark where relevant;
- file checksum and byte size at acquisition;
- any transformations before ingestion;
- rights evidence and restrictions;
- custody notes for physical scans/manuscripts.

## 5. Immutable and derived objects
Immutable or append-only: original FileAsset, raw extraction version, source verification event, rights decision event, review decision, scholarly assessment, audit event. Derived/rebuildable: normalized search text, passage segmentation, thumbnails, OCR layout derivatives, embeddings, search indexes, cached AI answer. A derived object still records its lineage and version.

## 6. Multilingual text policy
- Preserve exact source text and Unicode code points.
- Store display text separately from normalized search text.
- Record normalization algorithm/version, language, script and direction.
- Arabic diacritics, hamza forms, alif variants, ta marbuta, Persian/Urdu letters, ligatures and punctuation are not discarded from the source representation.
- Transliteration is a derived representation with scheme/version and must not replace original script.
- Translation is a distinct TextVersion with translator attribution and source citation.
- Mixed-language blocks may carry language per block or span.

## 7. Rights-aware access
- Unknown rights do not imply unrestricted reuse.
- Enforce rights/access filters in downloads, search, vector retrieval, AI context assembly and exports.
- A user may be allowed to view metadata but not download or quote full text.
- Record any permitted excerpt/quotation policy and attribution requirement.
- Rights changes trigger index visibility refresh and cache invalidation.

## 8. Retention and deletion
- Keep cited/audited scholarly records by default.
- Retire records rather than hard-delete when referenced.
- Legal takedown or privacy erasure follows a documented case, actor, reason, affected assets/derivatives and audit record.
- Delete derived indexes/caches when required; preserve non-sensitive audit evidence of the action.
- Backups have defined retention and secure disposal schedules.
