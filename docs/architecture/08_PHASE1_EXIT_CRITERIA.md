# Phase 1 Exit Criteria and Traceability

| Roadmap requirement | Design artifact/section | Completion condition |
|---|---|---|
| Domain-driven application structure | 00 §4; 01 | Ownership, dependency direction, service contracts and app creation policy documented. |
| Core database architecture | 00 §5; 02 | PostgreSQL conventions, PKs, types, constraints, FK/delete rules and migration approach documented. |
| Research entity architecture | 00 §6; 02 C | Canonical identity, aliases, identifiers, relationships, assertions and evidence defined. |
| Source and citation architecture | 00 §7; 02 A/C; 03 | Source, acquisition, rights, verification, citation and locator contracts defined. |
| Book and edition relationships | 00 §7.1; 02 A | Work/Edition/Volume and contributor roles defined. |
| User and permission architecture | 00 §9; 04 | Roles, scoped grants, object permissions and session boundaries defined. |
| File storage architecture | 00 §8.1; 04 | FileAsset, private storage, immutable originals, upload controls and recovery defined. |
| Search infrastructure architecture | 00 §10; 05 | Lexical/vector/hybrid pipeline, versioning, rights filters and evaluation defined. |
| AI service architecture | 00 §11; 05 | Provider boundary, execution trace, citation evidence contract and epistemic safety defined. |
| Knowledge graph architecture | 00 §12; 05 | Relational graph model, provenance, temporal and epistemic status defined. |
| Task processing architecture | 00 §13; 06 | Lifecycle, retries, heartbeat/lease, idempotency and outbox defined. |
| Audit and provenance architecture | 00 §14; 06; 07 | Append-only event families and separation of verification/review/assessment defined. |
| Required metadata | 00 §7.3; 03 | Every field in user's governance list mapped to an owning entity and missingness state. |
| Entire final research scope | 00 §15; 02 F | Quran/Tafsir, Hadith/Isnad, Fiqh, Aqidah, Tasawwuf, Seerah/history, linguistics, manuscripts have extension contracts. |
| Avoid foundational redesign | 00 §§4–17; 02 | Specialized domains reuse stable identities, source, corpus, citation, evidence and audit services. |

## Closure notes
Phase 1 is a design phase. Its exit is a complete documented baseline and owner sign-off, not creation of every future research model. The source code and database remain unchanged until the next implementation phase is explicitly authorized. A later implementation plan must map existing records/fields to the target schema and include non-destructive migrations, reconciliation, rollback and tests.

## Additional mandatory scholarly-safety exit criterion

| Roadmap requirement | Design artifact/section | Completion condition |
|---|---|---|
| Hadith citation, matn, isnad and grading verification | 18; 05; 13 | Verification dimensions are separate; model-generated grades and fabricated isnad/citations are prohibited; evidence IDs are server-validated; disagreement and abstention are explicit; automated acceptance tests are specified; rights and OCR provenance gates are included. |

The Hadith Verification Gate is a design requirement. Its automated tests and runtime enforcement belong to the implementation phase(s) assigned by the Master Roadmap; Phase 1 must not implement them.
