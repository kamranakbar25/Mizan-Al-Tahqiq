# Mizan al-Tahqiq — ميزان التحقيق
Milestone 1: Digital Library and first-book ingestion.

## Included
- Django 5.2, PostgreSQL configuration, REST API and admin.
- Authors, publishers, books, editions and volumes.
- PDF upload, metadata inspection and SHA-256 fingerprint.
- Page-wise embedded text extraction and page status.
- OCR-required classification for pages with no embedded text.
- Extracted-page search and automated tests.

## Not implemented in this milestone
Arabic OCR inference, OCR correction UI, Qdrant, RAG/LLM, Quran/Hadith/Fiqh/Tasawwuf structured modules. They are later milestones and are not represented as complete.

## Windows installation
```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```
Edit `.env` with PostgreSQL credentials and a strong SECRET_KEY. Create database `mizan_al_tahqiq` in PostgreSQL, then run:
```powershell
python manage.py check
python manage.py makemigrations library
python manage.py migrate
python manage.py createsuperuser
python manage.py test library
python manage.py runserver
```
Open dashboard http://127.0.0.1:9000/ and admin http://127.0.0.1:9000/admin/.

## First PDF workflow
1. In admin create an Author and Book; enter only verified metadata.
2. Create an Edition/Volume only if known. Do not guess missing details.
3. Add a Document and upload the PDF.
4. Use authenticated `POST /api/documents/{uuid}/inspect/`.
5. Use authenticated `POST /api/documents/{uuid}/ingest/`.
6. Search extracted text with `GET /api/search/pages/?q=phrase`.
7. Inspect page records at `GET /api/documents/{uuid}/pages/`.

## API endpoints
`/api/authors/`, `/api/publishers/`, `/api/books/`, `/api/editions/`, `/api/volumes/`, `/api/documents/`, `/api/search/pages/?q=...`. Document actions: `inspect/`, `ingest/`, `pages/`.

## Data integrity
`pdf_page_number` is the PDF's 1-based page index, not a printed page number. Printed page metadata remains blank unless verified. Original uploaded PDF is read, not modified. `ocr_required` means embedded text was not found; OCR has not run. Extracted content is machine-extracted and unverified. Re-ingestion replaces page extraction rows for that document. Back up before reprocessing if manual annotations are added later.

## Production security
Before network exposure set DEBUG=False, secure SECRET_KEY, HTTPS, secure cookies, restricted ALLOWED_HOSTS, private media delivery, backups, upload limits and access control. Debug media serving is development-only.
