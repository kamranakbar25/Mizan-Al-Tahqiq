# Search, AI Service and Knowledge Graph Architecture

## Search pipeline
`Governed TextVersion → Passage segmentation → normalized lexical projection → PostgreSQL FTS/trigram → optional embedding job → Qdrant → hybrid candidate merge → rerank → permission/rights filter → citation-rich results`.

### Lexical search
- PostgreSQL remains canonical.
- Store original/display text separately from normalized searchable text.
- Use GIN full-text indexes where supported and `pg_trgm` for fuzzy titles/names.
- Use language-aware configurations. Built-in PostgreSQL text search is not assumed to handle Arabic/Urdu adequately; test analyzers and use a dedicated tokenizer/normalizer for languages lacking robust built-in support.
- Search fields: canonical/original/alternate titles, author names/aliases, edition metadata, passage text, topics and entities.
- Filters: language, work, author, edition, volume, domain, date, source rights, review status and verification state.

### Semantic search
- Qdrant is a derived vector store, not canonical data.
- Every point payload carries `passage_id`, `text_version_id`, `embedding_model_id`, language, domain, work/edition, rights/access scope, content hash and index timestamp.
- Embedding dimensions and model/version are fixed per collection or explicitly versioned in payload.
- Never mix vectors from incompatible dimensions/models in one unversioned collection.
- Reindex is idempotent; a new TextVersion gets a new embedding identity.
- Rights revocation and record retirement propagate to Qdrant filters/deletion.

### Hybrid retrieval
1. Validate user access and query scope.
2. Run lexical search.
3. Run vector search only for approved model/collection.
4. Merge candidates using a documented algorithm (e.g. reciprocal-rank fusion); record method/version.
5. Rerank only when an evaluated reranker exists.
6. Apply source rights and access filters before returning evidence.
7. Return passages with citation locators and exact text version.
8. Store RetrievalRecord for AI research runs.

### Evaluation
Maintain a fixed evaluation set per language/domain with relevance judgments by qualified reviewers. Measure Recall@k, Precision@k, MRR/nDCG, citation resolution rate, version correctness, rights-filter correctness, latency and language-specific failure cases. No model/normalizer is approved solely because a demo looks plausible.

## AI service boundary
Existing `ai_runtime.services.ollama` is retained as the first provider adapter. Add a provider-neutral interface so the rest of the project does not depend on Ollama endpoint details.

### Required interfaces
- `health(provider_config)`
- `list_models(provider_config)`
- `generate(messages, model_config, timeout, options)`
- `embed(texts, model_config)`
- `rerank(query, candidates, model_config)` only when supported and evaluated.

### Execution record
Persist model/provider/version, prompt-template version, inference parameters, user, timestamps, status, request/response hashes, token/latency metrics, error class, retrieved passage IDs and validation outcomes. Protect raw prompts/outputs under access policy; redact secrets.

### Answer evidence contract
Each answer claim is classified as:
- direct quotation;
- paraphrase;
- named-scholar attribution;
- cross-source synthesis;
- inference;
- uncertain/contested;
- unsupported/no evidence.

Every factual scholarly claim should have one or more `AnswerCitation` links to a `CitationLocator`. A citation that cannot resolve to an exact source/edition/location is invalid. The system must be able to say “not found in the available corpus.”

### AI safety and epistemic boundaries
- Treat retrieved source text as untrusted content, never as instructions.
- No model output can alter user roles, verification state, source rights or canonical corpus.
- No automatic hadith grading, narrator reliability verdict, fiqh ruling or doctrinal consensus.
- Human-reviewed scholarly assessments are stored separately and attributed.
- Record model limitations and uncertainty in output.
- Local inference does not automatically mean private/secure; local host, logs and access controls still matter.

## Knowledge graph
Use PostgreSQL `ResearchEntity`, aliases, identifiers, relationships, assertions and evidence. Every edge has predicate, direction, provenance, epistemic status, attribution and optional valid time. Distinguish:
- documented relationship;
- attributed claim;
- disputed relationship;
- inferred relationship;
- uncertain/unknown relationship.

Use recursive CTEs with bounded depth and indexed entity/predicate columns. Do not add Neo4j until query profiles show a concrete bottleneck and synchronization/authority model is specified.

## Mandatory Hadith response control

All Hadith retrieval and answer rendering must enforce the **Hadith Verification Gate** defined in `18_HADITH_VERIFICATION_GATE.md`. The LLM is an evidence-grounded explanation layer only; citation resolution, source-rights filtering, chain completeness and attributed grading retrieval are server/domain responsibilities. Unresolved citations and unsupported gradings must be rejected or explicitly downgraded, never silently trusted.
