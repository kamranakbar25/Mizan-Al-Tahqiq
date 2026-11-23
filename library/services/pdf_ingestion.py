import hashlib
import pymupdf as fitz
from django.utils import timezone
from library.models import Document,Page,IngestionRun

def sha256_file(path):
 h=hashlib.sha256()
 with open(path,"rb") as f:
  for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
 return h.hexdigest()
def inspect_pdf(path):
 with fitz.open(path) as pdf:
  if pdf.is_encrypted: raise ValueError("Encrypted PDFs are not supported in this version.")
  return {"page_count":pdf.page_count,"metadata":{str(k):str(v or "") for k,v in (pdf.metadata or {}).items()},"is_encrypted":False}
def ingest_document(document):
 run=IngestionRun.objects.create(document=document,status="running")
 document.status="processing"; document.error_message=""; document.save(update_fields=["status","error_message"])
 try:
  document.sha256=sha256_file(document.file.path)
  with fitz.open(document.file.path) as pdf:
   if pdf.is_encrypted: raise ValueError("Encrypted PDFs are not supported.")
   run.total_pages=pdf.page_count; run.save(update_fields=["total_pages"])
   document.pages.all().delete()
   for i,p in enumerate(pdf):
    try:
     txt=p.get_text("text",sort=True).strip(); wc=len(txt.split()); state="text_extracted" if txt else "ocr_required"
     Page.objects.create(document=document,pdf_page_index=i,pdf_page_number=i+1,width_points=p.rect.width,height_points=p.rect.height,rotation=p.rotation,extracted_text=txt,text_status=state,word_count=wc)
     if txt: run.text_pages+=1
     else: run.ocr_required_pages+=1
    except Exception as e:
     Page.objects.create(document=document,pdf_page_index=i,pdf_page_number=i+1,text_status="error",extraction_error=str(e)); run.error_pages+=1
    run.processed_pages+=1
    if run.processed_pages%25==0: run.save(update_fields=["processed_pages","text_pages","ocr_required_pages","error_pages"])
  run.status="completed"; run.report={"sha256":document.sha256,"total_pages":run.total_pages,"text_pages":run.text_pages,"ocr_required_pages":run.ocr_required_pages,"error_pages":run.error_pages,"note":"No OCR has been run; image-only pages are flagged for the OCR milestone."}
  document.pdf_page_count=run.total_pages; document.status="completed"; document.processed_at=timezone.now(); document.save(update_fields=["sha256","pdf_page_count","status","processed_at"])
 except Exception as e:
  run.status="failed"; run.error_message=str(e); document.status="failed"; document.error_message=str(e); document.save(update_fields=["status","error_message"])
 finally:
  run.finished_at=timezone.now(); run.save()
 return run
