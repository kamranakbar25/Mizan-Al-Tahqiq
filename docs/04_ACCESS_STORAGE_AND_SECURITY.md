# Access Control, File Storage and Security Architecture

## Access control
Use the existing Django authentication user as the identity source. Do not duplicate password/session management.

### Roles and baseline capabilities
| Capability | Owner | Administrator | Researcher | Text Reviewer | Source Verifier | Scholar/Assessor | Read-only |
|---|---:|---:|---:|---:|---:|---:|---:|
| Manage users/roles | Yes | Delegated | No | No | No | No | No |
| Upload/manage source records | Yes | Yes | Draft/upload | No | Limited | No | No |
| Read permitted corpus | Yes | Yes | Yes | Assigned | Yes | Yes | Yes |
| Edit bibliographic metadata | Yes | Yes | Draft | No | No | No | No |
| Review/correct text | Yes | Delegated | No by default | Assigned | No | No | No |
| Verify source provenance/rights | Yes | Delegated | No | No | Assigned | No | No |
| Create scholarly assessments | Yes | Delegated | Draft | No | No | Scoped | No |
| Publish/release research records | Yes | Delegated | By policy | No | By policy | By policy | No |
| View audit trail | Yes | Scoped | Own/allowed | Own/assigned | Own/assigned | Own/assigned | No |

Roles are composable and scope-limited. A person’s role does not itself prove scholarly qualification. A scholar/assessor profile records declared field, institution/credentials, source evidence and scope; the system does not independently certify religious authority.

### Permission enforcement
- Deny by default.
- Check action + object + scope at API/view/service layer.
- Never rely on hidden buttons or frontend route secrecy.
- Separate content access, download access, edit access, verification authority and publication authority.
- Audit grants, revocations and privileged actions.
- Protect staff/admin routes independently from researcher session.
- Existing `mizan_admin_sessionid` and `mizan_researcher_sessionid` separation is retained as a current design feature; test CSRF, logout isolation, cookie flags and privilege boundaries.

## File storage
### Logical zones
1. `quarantine/` — uploaded but not validated/cleared.
2. `originals/` — immutable original source files.
3. `derivatives/` — OCR images, page crops, thumbnails and converted derivatives.
4. `exports/` — generated research exports with access controls.
5. `temporary/` — ephemeral processing scratch, routinely cleaned.

### FileAsset identity
`sha256 + byte_size + storage_backend + storage_key + media_type + original_filename + asset_role + rights reference`. A byte-identical file can be referenced by multiple source/document records; deduplication must not collapse bibliographic identity or provenance.

### Storage adapter
Required methods: save, open/read, exists, stat, checksum, governed delete, private download authorization. Keep local filesystem adapter first; object storage may be added without changing Document domain logic.

### Upload controls
- Validate extension and file signature, not extension alone.
- Enforce compressed and expanded size limits for DOCX/EPUB/archive formats.
- Reject path traversal and unsafe names; generate storage keys.
- Apply parser time/memory/page limits.
- Consider malware scanning and quarantine before processing.
- Never expose MEDIA_ROOT through public static serving.
- Use authorized download views or short-lived signed URLs.
- Keep secrets and `.env` out of Git/archive sharing.

### Backup and recovery
A recovery set includes PostgreSQL backup, original file storage snapshot, relevant derivatives, storage manifest/checksums and deployment configuration (excluding secrets from unsecured copies). Qdrant can be rebuilt but backup may reduce recovery time. Test DB/file consistency and restore a sample original file by checksum. Retain backup encryption, access control and off-machine copy.

## Production security baseline
- `DEBUG=False`; strong secret manager/env secrets; restricted ALLOWED_HOSTS.
- HTTPS; secure session and CSRF cookies; HSTS after deployment validation.
- BasicAuthentication disabled or TLS-only in production; session auth with CSRF.
- Rate limiting for login, uploads, search and expensive AI endpoints.
- Upload caps, parser sandbox/timeouts and resource limits.
- Private media, least-privilege DB user, restricted DB network.
- Dependency/security updates and audit logging.
- Avoid logging passwords, tokens, full private source text or sensitive user data.
