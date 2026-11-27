# 18 — Hadith Verification Gate (HVG)

**Status:** Mandatory target-architecture control for the Hadith research domain  
**Applies to:** Hadith discovery, retrieval, citation, isnad display, grading display, AI answers, exports and API responses  
**Authority:** Human-attributed scholarly evidence and verified source records; never model confidence

## 1. Purpose

Prevent the platform from presenting an ungrounded hadith citation, invented matn, fabricated isnad, or AI-generated authenticity judgement as verified scholarship. The gate is a publication and response-control layer. It reduces risk; it cannot guarantee that every digitized source, OCR result, catalog record or historical scholarly judgement is itself error-free.

## 2. Non-negotiable rules

1. **No source record, no verified citation.** A hadith may be described as verified only when it resolves to an internal canonical record and one or more traceable source witnesses.
2. **No AI grading.** Model-generated authenticity labels, narrator verdicts, or synthetic consensus are never scholarly assessments and must never be stored or displayed as such.
3. **No invented isnad.** The model may not complete missing narrators, links, routes or transmission details. Missing, uncertain and disputed links remain explicit.
4. **No flattened disagreement.** Different scholars' gradings remain separately attributed and scoped. The system must not manufacture a consensus or silently choose one assessment.
5. **No citation by plausibility.** Collection name, book/chapter, hadith number, volume/page and URL are rendered only from validated source/locator records. LLM-authored references are untrusted suggestions until resolved.
6. **No OCR certainty laundering.** OCR-derived text is not silently treated as a verified source transcription. The text witness must retain extraction method, version, review status and page/locator provenance.
7. **No evidence, abstain.** If the system cannot resolve adequate evidence, it must say that it cannot verify the report from the available corpus and must not guess.
8. **No rights bypass.** Restricted or rights-unknown source material must not be exposed through search snippets, citations, exports, embeddings or model context beyond its permitted access policy.

## 3. Required domain records (logical contract)

The following are logical contracts. They do not authorize immediate database changes; physical schema is designed and implemented only in the appropriate roadmap phase.

- **HadithIdentity:** stable internal identity for a report/concept, distinct from a particular wording or transmission route. Identity merges require evidence and human review; never merge on name/text similarity alone.
- **HadithOccurrence / Route:** a source-specific occurrence or transmission route, linked to the source witness and preserving collection-specific identity.
- **MatnWitness:** exact source-attested wording, language, variant, text version, source edition, page/locator and transcription state. Preserve variants; do not overwrite one wording with another.
- **IsnadChain / IsnadLink:** ordered chain and individual narrator-to-narrator links, including explicit unknown, missing, interrupted, disputed or incomplete states. A missing link is data, not an invitation for model completion.
- **NarratorIdentity / NarratorAssertion:** stable narrator identity plus attributed biographical and critical assertions. Preserve alias/transliteration variants and identity uncertainty.
- **ScholarlyAssessment:** attributed assessment with scholar, source work, exact citation, assessment term as stated, scope (specific route/occurrence/wording or broader claim), method/context where known, date/period where known, and provenance.
- **EvidenceLink:** machine-checkable links from each displayed factual claim to the underlying source, witness, locator, route or scholarly assessment.
- **VerificationEvent:** append-only record of who/what checked a source/citation/transcription, when, against which edition and which verification protocol/version.

A single report may have multiple occurrences, matn witnesses, routes and conflicting scholarly assessments. Do not collapse these into one global grade.

## 4. Verification states

Use explicit, non-interchangeable states. Exact enum names may be finalized during physical schema design, but the meanings must remain:

- **Unreviewed:** ingested but not checked.
- **OCR-derived:** machine-extracted text awaiting verification.
- **Source-located:** a candidate source and locator have been found, but the transcription/citation is not fully checked.
- **Transcription-checked:** wording has been checked against the specified source witness/edition; this does not imply authenticity grading.
- **Citation-validated:** collection/edition and locator resolve to a real stored source record.
- **Scholarly-assessed:** one or more attributed scholarly assessments are recorded; this is not a universal platform verdict.
- **Disputed:** material conflict, identity uncertainty or assessment disagreement is present.
- **Insufficient-evidence:** evidence is incomplete or unavailable.

Verification of wording, validation of citation, completeness of isnad, narrator research, and scholarly grading are separate dimensions. One must not imply another.

## 5. Runtime response gate

Before an answer is rendered as a factual hadith result:

1. Retrieve only records allowed by the user's permissions and source-rights policy.
2. Resolve every candidate citation to an internal source/edition/locator record. Reject unresolved model-generated citations.
3. Resolve the quoted or paraphrased matn to a source-attested text witness and retain variant information.
4. If an isnad is requested, load the stored ordered chain. Display missing or disputed links explicitly; never ask the LLM to fill them.
5. Load scholarly assessments as separate attributed records. Preserve the scholar's actual terminology and scope; do not translate nuanced terms into a stronger universal verdict.
6. Attach evidence identifiers to every material factual claim (source wording, locator, narrator claim, grading, disagreement).
7. Run server-side validation of every evidence identifier and access rule before rendering.
8. If any mandatory check fails, downgrade the result to an explicit unverified/partial state or abstain. Do not show a green/verified badge.
9. Log retrieval set, model/provider and prompt/config version, validation outcome, abstention reason and rendered evidence IDs for audit.

The LLM's role is limited to explaining, translating or summarizing retrieved evidence with clear attribution. It is not the authority that validates citations, determines chain continuity, grades a hadith, or adjudicates scholarly disagreement.

## 6. User-facing presentation contract

- Distinguish **text/transcription status**, **citation status**, **isnad completeness**, and **scholarly assessments** in separate fields/labels.
- Show exact source edition and locator where available. Explain whether a locator is printed pagination, PDF page index, database identifier or another scheme.
- Show each grading with scholar attribution and cited work; where assessments conflict, show the conflict rather than a single synthesized grade.
- Label a platform-generated summary as a summary, not a quotation or scholarly ruling.
- If data is missing, say exactly what is missing (e.g. edition not checked, chain incomplete, no attributed grading found).
- Never present a generated translation as the original Arabic matn. Preserve original text and identify translation provenance.

## 7. Source acquisition and ingestion controls

- Record repository/provider (e.g. Shamela), the underlying bibliographic work/edition when identifiable, acquisition date/method, source URL or package identifier, checksum, rights/licence status and permitted uses.
- A repository copy is not automatically an authoritative critical edition. Keep repository provenance distinct from bibliographic edition provenance.
- Rights status is independent from scholarly verification. Unknown rights remain restricted until reviewed.
- OCR output must retain page image/source file reference, OCR engine/model/version, language/configuration, raw output and post-processing version. Human corrections are versioned and attributable.
- Never silently replace the original file or raw OCR. Corrections create new immutable versions.
- Low-confidence or structurally suspicious OCR (Arabic punctuation, diacritics, narrator names, numbers, isnad separators) is routed to human review before being quoted as checked text.

## 8. Failure and abstention policy

| Condition | Required behavior |
|---|---|
| Citation cannot resolve to a source record | Do not emit it as a citation; abstain or mark candidate/unverified |
| Matn is OCR-only and not checked | Label OCR-derived; do not claim checked wording |
| Isnad record is absent/incomplete | State that chain data is unavailable/incomplete; never synthesize it |
| No attributed grading exists | Say no grading was found in the available corpus; do not infer one |
| Conflicting gradings exist | Present attributed views and scope separately |
| Narrator identity is ambiguous | Preserve ambiguity; do not auto-merge or assert identity |
| Source rights prohibit exposure | Suppress restricted content and follow access policy |
| Evidence IDs fail server validation | Block factual result and log validation failure |

## 9. Minimum automated acceptance tests

| Test ID | Scenario | Expected result |
|---|---|---|
| HVG-001 | Model invents a collection/number citation | Citation resolver rejects it |
| HVG-002 | Valid source record but wrong locator | Citation validation fails; no verified citation |
| HVG-003 | Matn differs from selected witness | Variant/mismatch is flagged; quote is blocked or qualified |
| HVG-004 | Isnad contains a missing link | Missing link is displayed; model cannot fill it |
| HVG-005 | Model proposes a sahih/da'if label without assessment record | Label is rejected |
| HVG-006 | Two attributed scholars disagree | Both assessments remain visible with attribution and scope |
| HVG-007 | Grading applies to one route but answer generalizes to all routes | Scope validation blocks generalization |
| HVG-008 | Narrator names are similar but identity is unconfirmed | No automatic identity merge |
| HVG-009 | OCR-only transcription is requested as exact quotation | Response labels OCR status or abstains |
| HVG-010 | Evidence ID is fabricated or inaccessible | Server blocks rendering |
| HVG-011 | Rights-unknown source is retrieved by unauthorized user | Access filter suppresses it |
| HVG-012 | No supporting evidence exists | Explicit abstention; no guessed hadith |
| HVG-013 | Translation is requested | Original matn and translation are distinguished with provenance |
| HVG-014 | Audit trail is inspected | Retrieval, validation and rendered evidence are traceable |

## 10. Human governance and operational controls

- Define qualified reviewer roles and review scopes before scholarly verification workflows go live.
- Reviewer actions must be attributable and auditable; corrections never erase prior assessments.
- Escalate disputed identity, chain or grading issues rather than auto-resolving them.
- Maintain a correction/reporting workflow for users/researchers, with triage and append-only resolution history.
- Measure citation-resolution rate, evidence coverage, abstention rate, OCR correction rate, unresolved disagreement count and false-acceptance rate on a curated evaluation set.
- Do not optimize only for answer coverage. A correct abstention is preferable to a fabricated scholarly claim.

## 11. Limits and residual risk

This gate cannot prove that every source edition is authentic, every catalog entry is correct, every OCR correction is accurate, or every recorded scholar attribution is complete. It can ensure the platform does not knowingly upgrade unsupported model output into verified scholarship. Source-quality review, expert oversight, adversarial testing and ongoing correction remain mandatory.

## 12. Implementation boundary

This document specifies target behavior only. It does not create models, migrations, indexes, queues, UI, prompts or runtime code. Implementation must occur in the roadmap phase assigned to the Hadith domain and must have its own reviewed non-destructive implementation plan, backups, tests, reconciliation and rollback.
