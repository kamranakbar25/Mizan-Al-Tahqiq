# 10 — Access Control and Permission Matrix
**Status: architecture proposal; requires owner approval**

## 1. Principles
- Deny by default; least privilege; explicit grants; no trust based solely on UI hiding.
- Separate authentication (who signed in) from authorization (what they may do).
- Every sensitive action is checked server-side at object and scope level.
- Admin, researcher, reviewer, source curator and system worker are distinct capabilities; one person may hold multiple explicitly granted roles.
- AI service accounts and background workers receive narrow service permissions, not human superuser access.
- Research visibility is private by default. Sharing is explicit, scoped, revocable and auditable.

## 2. Proposed role catalogue
| Role | Intended responsibility | Default scope |
|---|---|---|
| Platform Owner | policy, role grants, system governance | entire private platform |
| System Administrator | technical operations, account/session administration | operational scope; scholarly edits not implied |
| Researcher | search, read, create private research notes/assertions | own workspace / granted collections |
| Senior Researcher | review research assertions and evidence | assigned domains/collections |
| Text Reviewer / Qari | review OCR/transcription and create correction versions | assigned documents/languages |
| Source Curator | catalog metadata, acquisition and source provenance | assigned collections |
| Rights Reviewer | rights assessment and access restrictions | assigned sources/assets |
| Auditor | read audit trails and compliance evidence | approved audit scope, read-only |
| Worker Service | process jobs and emit technical events | specific job types and assets |
| AI Service | generate/embed under explicit request context | read-only eligible context; no verification authority |

## 3. Action matrix (default recommendation)
Legend: A=allow within granted scope; R=read-only; C=conditional/approval; —=deny by default.

| Action | Owner | Admin | Researcher | Senior Researcher | Text Reviewer | Source Curator | Rights Reviewer | Auditor | Worker/AI |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Manage platform roles | A | C | — | — | — | — | — | R | — |
| Read public-to-workspace catalog | A | A | A | A | A | A | A | R | C |
| Create/edit work metadata | A | C | C | C | — | A | — | R | — |
| Upload/register source | A | C | C | C | C | A | — | R | C |
| Change rights decision | A | — | — | — | — | C | A | R | — |
| Run ingestion/OCR | A | C | C | C | C | C | — | R | A |
| Correct transcription | A | — | C | C | A | — | — | R | — |
| Approve textual review | A | — | — | C | C* | — | — | R | — |
| Create scholarly assertion | A | — | A | A | — | C | — | R | — |
| Assess scholarly assertion | A | — | — | A | — | — | — | R | — |
| Manage citation/evidence links | A | C | A | A | C | C | — | R | — |
| Export/download source bytes | A | C | C | C | C | C | C | R* | C |
| View audit events | A | C | own scope | assigned scope | assigned scope | assigned scope | rights scope | A | own events only |

`C` means a policy gate, separate approval, or explicit grant is required. `C*` requires separation of duties where feasible: a person should not approve their own correction. Auditor downloads should be exceptional, logged and separately authorized.

## 4. Scope model
Every grant should include:
- principal (user or service identity);
- role/capability;
- resource scope (whole platform, domain, collection, source, document, research workspace);
- allowed actions;
- grantor, reason, start/end time;
- revocation timestamp and audit event.

Avoid embedding role names as scattered boolean flags. Evaluate permissions with a centralized policy service, e.g. `has_permission(principal, action, resource, context)`.

## 5. Sensitive operation controls
- Rights restriction and revoked access take effect on every read, search, export and vector retrieval.
- AI prompts may only receive source passages the requesting principal is allowed to access.
- Workers re-check asset eligibility before processing; queued jobs do not preserve stale authorization indefinitely.
- Downloads use short-lived authorized delivery, never public media URLs for private originals.
- Bulk export, role changes, rights decisions, deletion, restore and audit export require enhanced logging.
- Break-glass admin access is time-bound, reasoned and reviewed.

## 6. Session and account notes
Current source snapshot shows separate admin/researcher session cookie names. Preserve this as a session-boundary control, but do not mistake it for object-level authorization. Session rotation, CSRF, secure cookie flags, timeout, password reset and MFA policy require explicit deployment/security review.

## 7. Decisions still required
Owner must approve role names, whether senior researcher may approve others' work, whether text reviewers may self-approve, workspace sharing model, MFA requirement, session duration, break-glass policy and retention of audit events.
