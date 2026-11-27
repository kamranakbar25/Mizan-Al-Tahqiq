# 15 — Phase 1 Consolidated Owner Decision Sheet
**Please return one response containing all decisions.** No implementation is authorized by selecting these recommendations; this is architecture approval only.

## A. P0 contracts
For each item choose **Approve** or **Amend** and add a short note only if needed.

| ID | Recommended decision | Your decision |
|---|---|---|
| P0-01 Text lifecycle | Approve immutable TextVersion; corrections create new versions; review references exact version | Approve / Amend |
| P0-02 File identity | Approve additive FileAsset; keep Document.file during transition | Approve / Amend |
| P0-03 Bibliography | Approve Person + role-bearing contributor links; preserve existing IDs | Approve / Amend |
| P0-04 Source governance | Approve separate SourceRecord, acquisition, rights and verification event streams | Approve / Amend |
| P0-05 Citation | Approve Citation + scheme-specific CitationLocator; offsets bind exact text version | Approve / Amend |
| P0-06 Ancestry | Approve Work → Edition → Volume → Document consistency | Approve / Amend |

## B. Access and governance
| ID | Recommendation | Your decision |
|---|---|---|
| D-01 | Private-by-default research workspace; explicit sharing | Approve / Amend |
| D-02 | Deny-by-default object/scope permissions | Approve / Amend |
| D-03 | Separate Platform Owner, System Admin, Researcher, Senior Researcher, Text Reviewer, Source Curator, Rights Reviewer, Auditor and service identities | Approve / Amend |
| D-04 | Reviewer cannot approve own correction where separation of duties is feasible | Approve / Amend |
| D-05 | Unknown/unreviewed rights restrict source bytes, indexing and AI use until assessed | Approve / Amend |
| D-06 | AI output is always unverified unless separately assessed by an authorized scholar | Approve / Amend |
| D-07 | Audit events append-only; corrections via compensating events, not silent mutation | Approve / Amend |
| D-08 | Unknown/not_checked/not_applicable/disputed/inferred/redacted are distinct metadata states | Approve / Amend |

## C. Operations
| ID | Recommendation | Your decision |
|---|---|---|
| D-09 | Job lease + heartbeat + idempotency + attempt history before scaling OCR | Approve / Amend |
| D-10 | PostgreSQL is authoritative; Qdrant/vector indexes are derived and rebuildable | Approve / Amend |
| D-11 | Backup/restore policy and RPO/RTO must be approved before production corpus use | Approve / Amend |
| D-12 | No destructive migration; additive/backfill/reconcile/rollback sequence required | Approve / Amend |

## D. Response format
You can reply compactly, for example:

`P0: all approve. D-01 to D-12: all approve.`

If anything needs amendment, list only its ID and the change. This is the single consolidated owner review. Phase 1 remains open until decisions are recorded and the exit checklist is verified.


## Recorded owner decision — 27 November 2026

- P0-01 through P0-06: **APPROVED**.
- D-01 through D-12: **APPROVED**.
- Conditions: see `17_OWNER_APPROVAL_RECORD_2026-11-27.md`.
- Approval applies to architecture direction only; Phase 1 remains open until live-schema reconciliation and exit verification pass.
