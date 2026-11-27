# Phase 1 Architecture Decision Register

| ADR | Decision | Status | Consequence |
|---|---|---|---|
| ADR-001 | Modular Django monolith | Accepted in Phase 0 | Keep current deployment shape; logical domain boundaries first. |
| ADR-002 | PostgreSQL authoritative | Accepted in Phase 0 | Vector/search/AI outputs are derived. |
| ADR-003 | Preserve source identity/provenance | Accepted in Phase 0 | Immutable originals and versioned text. |
| ADR-004 | OCR subsystem belongs to Phase 3 | Accepted in Phase 0 | Phase 1 designs interfaces/data lifecycle only. |
| ADR-005 | Ollama behind `ai_runtime` adapter | Accepted in Phase 0 | Provider-neutral interface target. |
| ADR-006 | Vector search supplemental | Accepted in Phase 0 | Qdrant rebuildable; no claim of completed semantic retrieval. |
| ADR-007 | Server-side authorization | Accepted in Phase 0 | Role/action/object matrix defined in Phase 1. |
| ADR-008 | Environment-specific secrets/config | Accepted in Phase 0 | No secrets in source; production hardening required. |
| ADR-009 | Original files require separate backup | Accepted in Phase 0 | DB/file recovery coordinated. |
| ADR-010 | Background work recoverable/observable | Accepted in Phase 0 | Heartbeat/lease target replaces fixed stale-time assumption. |
| ADR-011 | Work/Edition/Volume separation | Phase 1 baseline | Contributors have explicit roles; document ancestry validated. |
| ADR-012 | TextVersion and Passage are canonical text units | Phase 1 baseline | Raw/corrected/normalized/translation never overwrite each other. |
| ADR-013 | Citation + CitationLocator | Phase 1 baseline | Printed pagination and PDF index are distinct. |
| ADR-014 | ResearchEntity + attributed assertions/evidence | Phase 1 baseline | Disagreement and epistemic status preserved. |
| ADR-015 | Rights, verification, review are separate axes | Phase 1 baseline | Independent state machines and events. |
| ADR-016 | FileAsset abstraction and private storage | Phase 1 baseline | Storage backend can evolve without domain rewrite. |
| ADR-017 | PostgreSQL graph first | Phase 1 baseline | Graph DB deferred pending evidence. |
| ADR-018 | Hybrid search with version-bound vectors | Phase 1 baseline | Qdrant payload traces exact text version and rights. |
| ADR-019 | AI output is non-authoritative | Phase 1 baseline | Human scholarly assessment required for verified records. |
| ADR-020 | Database queue + lease/heartbeat + outbox | Phase 1 baseline | External queue deferred until scale requires. |
| ADR-021 | Append-only audit event families | Phase 1 baseline | No silent edits to verification/review/assessment history. |
| ADR-022 | Domain apps introduced incrementally | Phase 1 baseline | Avoid empty apps and circular dependencies. |
| ADR-023 | Metadata missingness explicit | Phase 1 baseline | Unknown/not-applicable/not-checked/disputed; never guessed. |

Change procedure: record context, alternatives, decision, consequences, affected roadmap phase, data migration/rollback, test plan and owner/date. Master roadmap names/order/scope are immutable.
