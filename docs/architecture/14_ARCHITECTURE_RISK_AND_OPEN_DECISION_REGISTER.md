# 14 — Architecture Risk and Open Decision Register
**Status: review draft; no risk is considered accepted until owner decision is recorded.**

| ID | Risk / question | Impact | Recommended mitigation | Owner decision |
|---|---|---|---|---|
| R-01 | Source snapshot may differ from live DB | Invalid migration plan | Live schema introspection and migration graph verification before implementation | Pending |
| R-02 | Book/Work semantics ambiguous in existing data | Bibliographic identity errors | Preserve IDs; explicit mapping and ambiguous queue | Pending |
| R-03 | Document has independent Work/Edition/Volume FKs | Incorrect ancestry | Add consistency validation and exception report before constraint | Pending |
| R-04 | FileField and FileAsset coexistence | Broken media paths | Additive migration, dual-read, checksum verification, rollback window | Pending |
| R-05 | Page.extracted_text duplicates ExtractionVersion | Competing text truth | Define compatibility projection and single selected version | Pending |
| R-06 | ReviewRecord stores reviewed text | History ambiguity | Decision references exact immutable version; correction creates new version | Pending |
| R-07 | No first-class citation locator | Inaccurate citations | Scheme-specific locator with printed/PDF/folio distinctions | Pending |
| R-08 | Rights metadata may be incomplete | Unauthorized access/indexing | Unknown means restricted/pending; rights gate at retrieval/export | Pending |
| R-09 | Existing job stale detection lacks heartbeat | Lost/duplicated long OCR work | Lease, heartbeat, idempotency and attempt history | Pending |
| R-10 | Qdrant may be mistaken as authoritative | Stale/misleading search | PostgreSQL canonical; vectors rebuildable and version-bound | Pending |
| R-11 | AI output may be mistaken as verified scholarship | Scholarly misinformation | AI output unverified; evidence trace and human assessment | Pending |
| R-12 | Roles may be too broad | Data leakage or unauthorized edits | Object/scope grants, deny-by-default, audit | Pending |
| R-13 | Audit and retention requirements undefined | Inability to reconstruct changes | Append-only event families and owner-approved retention | Pending |
| R-14 | Large future domain scope causes premature app sprawl | Complexity | Modular monolith; create domain apps when roadmap phase requires | Pending |
| R-15 | Date/name normalization introduces false certainty | Historical inaccuracies | Preserve source form, calendar, precision and disputed status | Pending |

## Open decisions before Phase 1 closure
1. Approve/amend P0-01 to P0-06.
2. Confirm proposed role catalogue and permission matrix.
3. Approve default-private workspace and source access policy.
4. Approve rights states and whether unknown rights blocks indexing/AI use (recommendation: yes).
5. Approve backup RPO/RTO, retention and recovery ownership.
6. Approve source/text/research audit retention.
7. Confirm supported citation locator schemes for first implementation scope.
8. Confirm metadata missingness vocabulary.
9. Confirm whether all future domain extensions above are within the unchanged master roadmap scope.
10. Record owner, date and rationale for every accepted/rejected decision.
