# Domain Boundaries and Service Contracts

## Design rule
A domain owns its data and rules. Other domains call its public service/query interface; they do not write directly to its internal tables. Shared concepts (Person, Work, SourceRecord, Document, TextVersion, Passage, Citation, ResearchEntity) have one canonical owner.

## Domain ownership
| Domain | Owns | Public service contracts |
|---|---|---|
| accounts | roles, memberships, grants | `has_permission(user, action, object)`; `grant_role(...)`; `revoke_role(...)` |
| catalog | people, works, contributors, publishers, editions, volumes | `resolve_person`; `register_work`; `attach_contributor`; `resolve_edition` |
| sources | source records, acquisition, rights, verification | `record_acquisition`; `record_rights_decision`; `verify_source`; `get_source_manifest` |
| library | digital document lifecycle and FileAsset links | `register_document`; `validate_asset`; `inspect_document`; `get_document_manifest` |
| corpus | content units, text versions, blocks, passages, reviews | `create_text_version`; `approve_text`; `create_corrected_version`; `segment_passages` |
| citations | citations and locators | `resolve_citation`; `create_locator`; `render_citation` |
| research_core | entities, relations, assertions, evidence | `resolve_entity`; `assert_relationship`; `record_assertion`; `attach_evidence` |
| domain apps | specialized domain records | Domain-specific commands that call shared citation/evidence services |
| search | lexical/vector index projections | `index_text_version`; `remove_index_projection`; `hybrid_search` |
| ai_runtime | model/provider adapter | `generate`; `embed`; `health`; `list_models` |
| workflows | jobs, attempts, leases, outbox | `enqueue`; `claim`; `heartbeat`; `complete`; `retry_or_fail` |
| governance | audit events and policy controls | `record_event`; `get_audit_trail`; `apply_retention_policy` |

## Dependency rules
- `catalog` must not depend on `hadith`, `fiqh`, `quran`, `tasawwuf` or AI.
- `sources` may reference catalog and files but must not decide scholarly meaning.
- `corpus` depends on library/source identity and owns text-version semantics.
- `citations` depends on catalog/library/corpus, not on any one specialized research domain.
- `research_core` depends on citation and catalog; domain apps extend it.
- `search` consumes corpus and research projections; it never becomes authoritative.
- `ai_runtime` has no write authority over verified source/research records.
- `workflows` invokes domain services and stores task state; domain apps do not implement their own ad-hoc queue.
- `governance` receives events; it does not become a shadow database for business data.

## Transaction boundary
A single domain command should be atomic within PostgreSQL. Cross-domain work uses an outbox event and idempotent consumer. Never hold a database transaction open during OCR, LLM inference, network calls or long file processing.

## API contract principles
- REST resources expose stable identifiers and explicit status/version fields.
- Mutating commands validate object-level permissions server-side.
- API responses identify machine extraction vs reviewed text.
- Search responses include citation locator, edition, volume, printed page and PDF page as separate fields when known.
- AI responses return citations and evidence-validation status, not just prose.
