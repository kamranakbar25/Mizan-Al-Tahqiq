# 20 — Source Snapshot Reconciliation Report
**Version 0.6 | Snapshot inspected:** `Mizan-Al-Tahqiq_SAFE_AUDIT_20261127_121650.zip`

## Evidence boundary
This is a static inspection of the uploaded source ZIP. It is not live PostgreSQL introspection, not a live `showmigrations` result and not proof that the current local checkout matches the archive.

## Model inventory in snapshot
`library/models.py` defines 15 model classes:

- `Author`
- `Publisher`
- `Book`
- `Edition`
- `Volume`
- `KnowledgeCategory`
- `SourceRecord`
- `SourceVerificationEvent`
- `Document`
- `Page`
- `IngestionRun`
- `ProcessingJob`
- `ExtractionVersion`
- `TextBlock`
- `ReviewRecord`

`ai_runtime/models.py` contains no database models in this snapshot.

## Migration files present in snapshot
- `library.migrations.0001_initial.py`
- `library.migrations.0002_universal_ingestion_v1.py`
- `library.migrations.0003_alter_extractionversion_engine_version.py`
- `library.migrations.0004_book_alternate_titles_book_original_title_and_more.py`
- `library.migrations.0005_sourceverificationevent.py`
- `ai_runtime.migrations.0001_initial.py`
- `ai_runtime.migrations.0002_alter_ocrjob_status.py`
- `ai_runtime.migrations.0003_delete_ocrjob.py`


The `ai_runtime` migration history includes the initial OCRJob creation, a status alteration and a later OCRJob deletion migration. This is consistent with the documented retirement pattern: historical migrations remain while the current model is removed. The library app snapshot includes five migration files.

## What this can establish
- Snapshot model inventory and migration filenames.
- The current model class names visible in the archived source.
- Historical OCRJob migration presence in the archive.

## What this cannot establish
- Which migrations are applied to the user's live PostgreSQL database.
- Whether the live database has drifted from the archive.
- Actual table/column/index/constraint state or row-level ancestry integrity.
- Whether the user's current working tree has merged Review Pack 0.6.

## Required next evidence
Run `tools/phase1_readonly_audit.py` from the actual project root. It uses Django's configured connection and migration loader to collect live introspection without schema/data writes. Compare its output with `02_MASTER_DATABASE_SCHEMA.md` and `09_CURRENT_TO_TARGET_MAPPING_AND_P0_REVIEW_0.3.md`.
