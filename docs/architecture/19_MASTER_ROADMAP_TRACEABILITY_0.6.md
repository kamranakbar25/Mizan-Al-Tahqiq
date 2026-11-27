# 19 — Master Roadmap Phase 1 Traceability Matrix
**Version 0.6 | Source:** Master Development Roadmap — Updated Edition (user-provided project source)

The 12 module names below are reproduced in the same order as the Master Development Roadmap. This matrix traces design coverage only; it does not claim implementation.

| # | Exact Phase 1 roadmap module | Architecture coverage | Assessment |
|---:|---|---|---|
| 1 | Domain-driven application structure | `00` §4; `01` domain ownership, dependency rules and service contracts | Documented |
| 2 | Core database architecture | `00` §5; `02` conventions, constraints, indexes, lifecycle and invariants | Documented |
| 3 | Research entity architecture | `00` §6; `02` §C and §F; `13` domain extension contracts | Documented; domain-specific schemas remain later-phase extensions |
| 4 | Source and citation architecture | `00` §7; `02` §A/§C; `03`; `11` source/citation workflows; `18` hadith evidence gate | Documented |
| 5 | Book and edition relationships | `00` §7.1; `02` §A; `09` current-to-target mapping | Documented; live ancestry reconciliation pending |
| 6 | User and permission architecture | `00` §9; `04`; `10` action/scope matrix | Documented; live authorization tests belong to implementation |
| 7 | File storage architecture | `00` §8.1; `02` §B; `04`; `11` acquisition/rights workflows | Documented; live storage inventory pending |
| 8 | Search infrastructure architecture | `00` §10; `05` search pipeline/evaluation; `02` §E | Documented; Qdrant remains derived/planned, not claimed operational |
| 9 | AI service architecture | `00` §11; `05` AI boundary/evidence contract; `02` §E; `18` verification gate | Documented; runtime enforcement belongs to Phase 13 and related later work |
| 10 | Knowledge graph architecture | `00` §12; `05` graph/provenance; `02` §C | Documented; graph implementation belongs to Phase 12 |
| 11 | Task processing architecture | `00` §13; `06`; `11` workflow H | Documented; lease/heartbeat implementation remains future work |
| 12 | Audit and provenance architecture | `00` §14; `03`; `06`; `12`; `17` approval conditions | Documented |

## Roadmap data-governance metadata trace
The roadmap requires: Original source, Author, Title, Publisher, Edition, Publication year, Volume, Page numbering system, Language, Source format, Rights/licence information, Acquisition information and Processing history. Ownership is mapped as follows:

| Roadmap metadata | Canonical owner / contract |
|---|---|
| Original source | `SourceRecord` + `SourceAcquisition` (`02` §A; `03`) |
| Author | `Person` + `WorkContributor` (`02` §A; `09`) |
| Title | Work/Edition/Document title statements (`02` §A; `12`) |
| Publisher | Publisher + Edition imprint (`02` §A; `12`) |
| Edition | Edition (`02` §A; `00` §7.1) |
| Publication year | Edition publication statement with calendar/precision (`02`; `12`) |
| Volume | Volume with parent consistency (`02`; `12`) |
| Page numbering system | `CitationLocator` scheme (`02` §C; `12`) |
| Language | Document/TextVersion language/script metadata (`02` §B; `12`) |
| Source format | FileAsset detected MIME/format (`02` §B; `04`) |
| Rights/licence | RightsRecord + decision events (`02` §A; `03`; `04`) |
| Acquisition information | SourceAcquisition (`02` §A; `03`; `11`) |
| Processing history | IngestionRun/WorkflowJob/Attempt + immutable TextVersion lineage (`02` §B/§D; `06`; `11`) |

## Scope boundary
Phase 1 defines architecture for the full permanent research scope. It does not implement Quran, Hadith, Fiqh, Tasawwuf, search, graph, AI, OCR or frontend modules. Those remain in their exact later roadmap phases. The Hadith Verification Gate is an architectural contract that supports the later Hadith and AI phases; it does not move those implementations into Phase 1.

## Result
All 12 Phase 1 module headings and all 13 explicitly listed source metadata fields have a documented architecture owner. The remaining blockers are live-environment evidence, repository consistency and formal exit review—not missing roadmap module headings.
