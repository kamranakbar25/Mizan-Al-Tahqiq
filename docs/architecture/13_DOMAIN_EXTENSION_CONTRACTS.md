# 13 — Research Domain Extension Contracts
**Purpose:** ensure specialized research areas reuse shared identity, source, corpus, citation, evidence, permissions and audit infrastructure.

## Shared invariant
No specialized domain creates a parallel Person, SourceRecord, Document, TextVersion, Citation or AuditEvent system. Domain records reference shared canonical identities and retain their own domain-specific semantics.

## Quran and Tafsir
- Stable Quran reference: canonical surah and ayah identifiers; text witness/reading and edition-specific text are separate.
- Tafsir work/commentary is a Work/Edition and its statements link to ayah ranges through CitationLocator.
- Revelation context (asbab al-nuzul), Makki/Madani, chronology and occasion are attributed assertions with evidence and disputed alternatives.
- Tafsir positions are scholar-attributed and versioned; do not collapse differences into one answer.
- Quran text variants/readings require explicit qira'at/witness identity; never silently normalize away differences.

## Hadith and Isnad
- Hadith identity, matn variants, source occurrence and individual transmission route are distinct entities.
- Isnad is an ordered chain of narrator occurrences/links, not a flat list of names.
- Narrator identity links to shared Person; narrator biography, teacher/student relations, dates and jarh/ta'dil statements are sourced assertions.
- Grading is an attributed assessment with scholar, method, source, date, rationale and scope; grades may differ by route, wording or scholar.
- Preserve Arabic matn variants and exact source locators. Never infer authenticity from an LLM response.

## Fiqh and Usul
- Madhhab, school lineage, question/mas'ala, opinion, ruling, evidence and usul principle are distinct concepts.
- A ruling records scholar, madhhab, context, conditions, date/period, source citations and disagreement.
- Do not represent one madhhab's answer as universal consensus.
- Comparative views retain original terminology and source wording.

## Aqidah
- Doctrine topic, attributed position, school/tradition, scholar, text and assessment remain distinct.
- Historical attribution and later interpretation are separately evidenced.
- Disputed classification is represented as competing assertions, not forced taxonomy.

## Tasawwuf
- Tariqa/tradition, silsila/lineage, shaykh, student, concept, practice and attributed teaching are distinct.
- Lineage links require source evidence and temporal context.
- Do not infer affiliation solely from a biographical mention or honorific.

## Seerah and Islamic history
- Event, participant, place, chronology/date range and report are distinct.
- Conflicting dates/routes/accounts coexist with source attribution and confidence.
- Hijri/Gregorian conversion is stored with conversion method and uncertainty, not false precision.

## Arabic linguistics
- Root, lemma, surface form, morphology, syntax, semantic sense and lexicon entry are distinct.
- Lexical/grammatical analysis links to exact text version and passage.
- Competing grammatical analyses can coexist with scholar/source attribution.

## Manuscripts and textual criticism
- Manuscript witness, repository shelfmark, codicological description, folio, hand, marginalia, variant reading and collation are distinct.
- Shelfmark is an external identifier, not a globally unique internal ID.
- Images/folios link to immutable FileAssets and exact locators.
- Collation statements cite both witnesses and preserve uncertainty.

## Cross-domain acceptance
Every domain extension must define: canonical IDs, ownership, source/citation requirements, evidence model, permission scope, temporal/uncertainty handling, audit events, search projection and migration/rollback plan before implementation.

## Hadith domain — mandatory verification contract

The Hadith domain must implement the verification and abstention requirements in `18_HADITH_VERIFICATION_GATE.md`: separate report identity, occurrence/route, matn witness, ordered isnad links, narrator assertions, attributed scholarly assessments and evidence links; preserve variant wording and disagreement; reject unresolved citations and AI-generated grades; and expose verification dimensions separately. This is a target contract, not authorization to create physical schema in Phase 1.
