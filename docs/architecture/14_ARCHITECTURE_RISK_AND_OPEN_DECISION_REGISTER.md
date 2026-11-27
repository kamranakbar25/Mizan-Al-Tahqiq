# 14 — Architecture Risk and Open Decision Register
**Status: owner-approved architecture mitigations; implementation and live-environment risks remain open until verified.**

| ID | Risk / question | Impact | Recommended mitigation | Owner decision |
|---|---|---|---|---|
| R-01 | Source snapshot may differ from live DB | Invalid migration plan | Live schema introspection and migration graph verification before implementation | OPEN — live evidence required |
| R-02 | Book/Work semantics ambiguous in existing data | Bibliographic identity errors | Preserve IDs; explicit mapping and ambiguous queue | MITIGATION APPROVED; data mapping later |
| R-03 | Document has independent Work/Edition/Volume FKs | Incorrect ancestry | Add consistency validation and exception report before constraint | MITIGATION APPROVED; live rows to reconcile |
| R-04 | FileField and FileAsset coexistence | Broken media paths | Additive migration, dual-read, checksum verification, rollback window | MITIGATION APPROVED; implementation plan later |
| R-05 | Page.extracted_text duplicates ExtractionVersion | Competing text truth | Define compatibility projection and single selected version | MITIGATION APPROVED; implementation plan later |
| R-06 | ReviewRecord stores reviewed text | History ambiguity | Decision references exact immutable version; correction creates new version | MITIGATION APPROVED; implementation plan later |
| R-07 | No first-class citation locator | Inaccurate citations | Scheme-specific locator with printed/PDF/folio distinctions | MITIGATION APPROVED; implementation plan later |
| R-08 | Rights metadata may be incomplete | Unauthorized access/indexing | Unknown means restricted/pending; rights gate at retrieval/export | MITIGATION APPROVED; source review later |
| R-09 | Existing job stale detection lacks heartbeat | Lost/duplicated long OCR work | Lease, heartbeat, idempotency and attempt history | MITIGATION APPROVED; implementation plan later |
| R-10 | Qdrant may be mistaken as authoritative | Stale/misleading search | PostgreSQL canonical; vectors rebuildable and version-bound | DECISION APPROVED |
| R-11 | AI output may be mistaken as verified scholarship | Scholarly misinformation | AI output unverified; evidence trace and human assessment | DECISION APPROVED; HVG specified |
| R-12 | Roles may be too broad | Data leakage or unauthorized edits | Object/scope grants, deny-by-default, audit | DECISION APPROVED |
| R-13 | Audit and retention requirements undefined | Inability to reconstruct changes | Append-only event families; exact retention window set before production | DIRECTION APPROVED; numeric policy deferred |
| R-14 | Large future domain scope causes premature app sprawl | Complexity | Modular monolith; create domain apps when roadmap phase requires | DECISION APPROVED |
| R-15 | Date/name normalization introduces false certainty | Historical inaccuracies | Preserve source form, calendar, precision and disputed status | MITIGATION APPROVED |

## Implementation planning items (already governed by approved direction)
1. Convert approved P0 contracts into a separately reviewed migration design when the relevant implementation phase begins.
2. Implement the approved permission matrix with server-side object/scope checks and tests.
3. Apply rights restrictions consistently to storage, processing, retrieval, export and AI context.
4. Set numeric backup RPO/RTO and retention periods before production corpus use.
5. Implement lease/heartbeat/idempotency/attempt history before scaling long-running OCR workloads.
6. Implement citation locator and evidence validation in the phases that introduce citation-bearing research outputs.
7. Implement the Hadith Verification Gate and its acceptance tests in the roadmap's Hadith/AI/verification phases.
8. Calibrate OCR/search confidence and quality thresholds using measured, manually reviewed samples.
9. Keep domain-specific extensions in their exact roadmap phases; do not create premature app sprawl.
10. For each implementation change, record owner, rationale, affected phase, migration/rollback plan and tests.

Phase 1 closure blockers are limited to evidence gates: live schema/migration reconciliation, exact roadmap traceability, final artifact consistency and exit review. Implementation risks above remain recorded for their respective later phases and do not imply that Phase 1 must implement those features.
