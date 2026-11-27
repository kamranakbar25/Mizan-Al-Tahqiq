# 12 — Metadata Governance and Data Quality
**Status: architecture contract proposal**

## 1. Required metadata ownership matrix
| Metadata | Canonical owner | Notes |
|---|---|---|
| Repository/collection | Collection / SourceRecord | Stable internal identifier and curator |
| Author/contributor | Person + WorkContributor / EditionContributor | Role and attribution certainty explicit |
| Title/original title/alternate title | Work / Edition / Document title statements | Preserve source spelling and language |
| Publisher | Publisher + Edition imprint statement | Publisher identity may be unresolved |
| Edition | Edition | Edition statement, number, place and date |
| Publication year/date | Edition publication statement | Support AH/CE, range, circa and unknown |
| Volume | Volume | Volume number/label and parent consistency |
| Printed page | CitationLocator | Never conflate with PDF page index |
| PDF page index/number | ContentUnit / locator | Zero/one-based convention explicitly stored |
| Folio/section/line | CitationLocator | Scheme-specific locator |
| Language/script/direction | TextVersion / Document | BCP-47 where practical; script and RTL/LTR separately |
| Format/MIME | FileAsset / Document | Detected format distinct from claimed extension |
| Rights/license/terms | RightsRecord + decision events | Unknown is not public domain |
| Acquisition origin/date | SourceAcquisition | Record provenance and evidence |
| Checksum/byte size | FileAsset | Algorithm + digest + size |
| Processing history | IngestionRun / WorkflowJob / JobAttempt | Pipeline/model version and timestamps |
| Text review status | TextReviewDecision | Separate from source verification |
| Source verification status | SourceVerificationEvent projection | Separate from rights and textual review |
| Scholarly assessment | AssertionAssessment | Domain-specific authority and rationale |

## 2. Missingness vocabulary
Every governed field should distinguish:
- `known`: value supported by evidence;
- `unknown`: not currently known;
- `not_checked`: not assessed yet;
- `not_applicable`: field does not apply;
- `disputed`: conflicting evidence exists;
- `inferred`: inferred value, with method and evidence;
- `redacted`: intentionally withheld under policy.

Do not store a guessed value as known. Do not turn empty string into an undocumented status.

## 3. Provenance requirements
For each significant metadata change retain actor/system, timestamp, prior/new value or structured diff, reason, evidence/source, and approval where required. Preserve original-script text and source-faithful spelling. Normalized/search forms are derived values and must not replace source form.

## 4. Data quality rules
- Stable IDs; no identity merge based only on string similarity.
- Controlled vocabularies for languages, scripts, formats, roles, rights states and review decisions.
- Date precision is never greater than source evidence.
- Cross-field consistency: Document.Volume must belong to Document.Edition and Document.Work.
- Citation locator must identify its locator scheme and target version when text offsets are used.
- Every vector/index projection records source TextVersion ID, embedding model/version and index generation.
- Every OCR/transcription correction retains the previous version.
- Rights state is checked before any downstream derivative is made available.
- Duplicate bytes may be deduplicated physically but provenance records remain distinct.

## 5. Data quality lifecycle
Ingest → validate → quarantine exceptions → curator resolve → publish to eligible workspace → monitor drift → record corrections. Exceptions should be first-class records with owner, severity, status and resolution evidence.

## 6. Retention and deletion
Original scholarly source bytes and audit events should not be hard-deleted by routine UI actions. Define legal takedown, rights revocation, account deletion, derived-index removal, backup expiry and retention exceptions separately. A deletion request must produce an impact plan across source, assets, text versions, passages, vectors, caches, citations and audit evidence before execution.

## 7. Open policy decisions
Owner approval required for retention periods, backup retention, legal takedown process, metadata change review, confidence thresholds, supported date calendars and language/script vocabularies.
