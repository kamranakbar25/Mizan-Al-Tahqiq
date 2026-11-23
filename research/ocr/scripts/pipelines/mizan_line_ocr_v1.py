"""
MIZAN LINE-WISE OCR PROTOTYPE v1
Run from qari-venv:
    python mizan_line_ocr_v1.py

Pipeline:
1. Render selected PDF pages.
2. Launch PaddleOCR text detection in ocr-venv (CPU by default).
3. Recognize each detected line crop with QARI in qari-venv.
4. Save raw per-line text, ordered transcript, JSON report, and detection overlay.

Nothing is silently deduplicated or corrected. All OCR is unverified.
"""

from __future__ import annotations

# Shared Mizan OCR paths
import sys as _sys
from pathlib import Path as _Path
for _parent in _Path(__file__).resolve().parents:
    if (_parent / "research" / "ocr" / "config" / "paths.py").is_file():
        _sys.path.insert(0, str(_parent))
        break
else:
    raise RuntimeError("Cannot locate Mizan project root.")
from research.ocr.config.paths import *


import json
import re
import subprocess
import sys
import time
import hashlib
from datetime import datetime, timezone
from pathlib import Path

import torch
import pymupdf
from PIL import Image
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info


# ---------------- CONFIG ----------------

BASE_DIR = PROJECT_ROOT
PDF_PATH = IHYA_VOL1_PDF
OCR_PYTHON = OCR_VENV_PYTHON
DETECTOR_SCRIPT = SCRIPTS_DIR / "detection" / "mizan_detect_lines.py"
OUTPUT_DIR = LINE_OCR_V1_DIR
PAGE_NUMBERS = [550, 650]  # 1-based PDF page numbers
RENDER_SCALE = 3.0
DETECTION_DEVICE = "cpu"   # Keeps Paddle detection away from the 8GB QARI GPU.
MAX_NEW_TOKENS_PER_LINE = 160
REPETITION_PENALTY = 1.08

MODEL_NAME = "NAMAA-Space/Qari-OCR-0.2.2.1-VL-2B-Instruct"

PROMPT = """Read the text visible in this image crop and transcribe it exactly.
Preserve the original language and script: English stays English; Arabic stays Arabic.
Do not translate, summarize, explain, complete missing words, or add commentary.
Do not repeat any word or line. Output only the text visible in this crop.
If the crop contains no readable text, output [unreadable]."""


# ---------------- HELPERS ----------------

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def get_page_image(pdf, page_number: int, destination: Path) -> dict:
    page = pdf.load_page(page_number - 1)
    pix = page.get_pixmap(
        matrix=pymupdf.Matrix(RENDER_SCALE, RENDER_SCALE),
        alpha=False,
    )
    image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    image.save(destination, format="PNG")
    return {
        "page": page_number,
        "page_index_zero_based": page_number - 1,
        "render_scale": RENDER_SCALE,
        "image_size": [image.width, image.height],
        "pdf_page_rect": [page.rect.x0, page.rect.y0, page.rect.x1, page.rect.y1],
    }


def run_detector(image_path: Path, page_number: int, page_dir: Path) -> Path:
    if not OCR_PYTHON.exists():
        raise FileNotFoundError(
            f"Cannot find PaddleOCR Python: {OCR_PYTHON}\n"
            "Check that ocr-venv exists in the project root."
        )
    if not DETECTOR_SCRIPT.exists():
        raise FileNotFoundError(f"Missing detector helper: {DETECTOR_SCRIPT}")

    command = [
        str(OCR_PYTHON),
        str(DETECTOR_SCRIPT),
        "--image", str(image_path),
        "--out-dir", str(OUTPUT_DIR),
        "--page", str(page_number),
        "--device", DETECTION_DEVICE,
    ]
    print("\nRunning PaddleOCR line detection...")
    subprocess.run(command, cwd=str(BASE_DIR), check=True)
    manifest_path = page_dir / "line_manifest.json"
    if not manifest_path.exists():
        raise RuntimeError(f"Detector did not create manifest: {manifest_path}")
    return manifest_path


def recognize_crop(model, processor, crop_path: Path):
    messages = [{
        "role": "user",
        "content": [
            {"type": "image", "image": str(crop_path.resolve())},
            {"type": "text", "text": PROMPT},
        ],
    }]
    prompt_text = processor.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    image_inputs, video_inputs = process_vision_info(messages)
    inputs = processor(
        text=[prompt_text],
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        return_tensors="pt",
    ).to(model.device)

    start = time.perf_counter()
    with torch.inference_mode():
        generated = model.generate(
            **inputs,
            max_new_tokens=MAX_NEW_TOKENS_PER_LINE,
            do_sample=False,
            use_cache=True,
            repetition_penalty=REPETITION_PENALTY,
            renormalize_logits=True,
        )
    elapsed = round(time.perf_counter() - start, 2)

    prompt_length = inputs["input_ids"].shape[1]
    new_tokens = generated[0][prompt_length:]
    token_count = int(new_tokens.shape[0])
    text = processor.decode(
        new_tokens,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=False,
    ).strip()

    del inputs, generated, new_tokens
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    return text, token_count, token_count >= MAX_NEW_TOKENS_PER_LINE, elapsed


def main():
    for required in (PDF_PATH, OCR_PYTHON, DETECTOR_SCRIPT):
        if not required.exists():
            raise FileNotFoundError(f"Required path not found: {required}")

    for folder in (
        OUTPUT_DIR,
        OUTPUT_DIR / "page_images",
        OUTPUT_DIR / "transcriptions",
        OUTPUT_DIR / "reports",
    ):
        folder.mkdir(parents=True, exist_ok=True)

    print("=" * 68)
    print("MIZAN - LINE-WISE OCR PROTOTYPE v1")
    print("=" * 68)
    print(f"PDF: {PDF_PATH}")
    print(f"QARI GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")
    print(f"Detection device: {DETECTION_DEVICE}")
    print(f"Pages: {PAGE_NUMBERS}")

    print("\nLoading QARI model...")
    model = Qwen2VLForConditionalGeneration.from_pretrained(
        MODEL_NAME,
        torch_dtype="auto",
        device_map="auto",
    )
    processor = AutoProcessor.from_pretrained(MODEL_NAME)
    model.eval()
    print("QARI loaded.")

    pdf = pymupdf.open(PDF_PATH)
    report = {
        "benchmark": "Mizan Line-wise OCR v1",
        "model": MODEL_NAME,
        "detector": "PP-OCRv5_server_det",
        "pdf": str(PDF_PATH),
        "pdf_sha256": sha256_file(PDF_PATH),
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU",
        "detection_device": DETECTION_DEVICE,
        "render_scale": RENDER_SCALE,
        "max_new_tokens_per_line": MAX_NEW_TOKENS_PER_LINE,
        "pages": [],
        "important_notice": (
            "OCR is machine-generated and unverified. Detected regions are not "
            "proof that every printed line was detected. Verify overlay and crops."
        ),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    try:
        for page_number in PAGE_NUMBERS:
            print("\n" + "=" * 68)
            print(f"PROCESSING PDF PAGE {page_number}")
            print("=" * 68)

            page_dir = OUTPUT_DIR / f"page_{page_number}"
            page_dir.mkdir(parents=True, exist_ok=True)
            image_path = OUTPUT_DIR / "page_images" / f"page_{page_number}.png"
            page_meta = get_page_image(pdf, page_number, image_path)

            manifest_path = run_detector(image_path, page_number, page_dir)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            lines = manifest.get("lines", [])

            page_text_parts = []
            line_results = []
            print(f"\nQARI recognition: {len(lines)} detected line regions")

            for index, line in enumerate(lines, start=1):
                crop_path = Path(line["crop_path"])
                print(
                    f"[{index}/{len(lines)}] {line['line_id']} "
                    f"box={line['bbox']} det_score={line.get('det_score')}"
                )
                try:
                    text, token_count, hit_limit, elapsed = recognize_crop(
                        model, processor, crop_path
                    )
                    line["recognized_text"] = text
                    line["generated_tokens"] = token_count
                    line["reached_token_limit"] = hit_limit
                    line["recognition_seconds"] = elapsed
                    line["recognition_status"] = (
                        "token_limit_review" if hit_limit else "recognized_review_required"
                    )
                    line_text_path = (
                        OUTPUT_DIR / "transcriptions"
                        / f"page_{page_number}_{line['line_id']}.txt"
                    )
                    line_text_path.write_text(text, encoding="utf-8")
                    line["text_file"] = str(line_text_path)
                    page_text_parts.append(text)
                    print(
                        f"    chars={len(text)} tokens={token_count} "
                        f"time={elapsed}s" + (" [LIMIT]" if hit_limit else "")
                    )
                except Exception as exc:
                    line["recognition_status"] = "failed"
                    line["recognition_error"] = repr(exc)
                    line["recognized_text"] = ""
                    page_text_parts.append("[RECOGNITION_FAILED]")
                    print(f"    ERROR: {exc!r}")

                line_results.append(line)

            # Keep every detected line and its output in reading order.
            combined_text = "\n".join(
                f"[{line['reading_order']:04d} | {line['line_id']} | "
                f"det={line.get('det_score')}] "
                f"{line.get('recognized_text', '')}"
                for line in line_results
            )
            combined_path = (
                OUTPUT_DIR / "transcriptions" / f"page_{page_number}_combined.txt"
            )
            combined_path.write_text(combined_text, encoding="utf-8")

            page_report = {
                **page_meta,
                "full_page_image": str(image_path),
                "detection_overlay": manifest.get("overlay_path"),
                "detected_line_count": len(lines),
                "recognized_line_count": sum(
                    1 for line in line_results
                    if line["recognition_status"] != "failed"
                ),
                "failed_line_count": sum(
                    1 for line in line_results
                    if line["recognition_status"] == "failed"
                ),
                "token_limit_line_count": sum(
                    1 for line in line_results
                    if line.get("reached_token_limit")
                ),
                "combined_text_file": str(combined_path),
                "lines": line_results,
                "status": "human_review_required",
            }
            report["pages"].append(page_report)
            page_report_path = (
                OUTPUT_DIR / "reports" / f"page_{page_number}_report.json"
            )
            page_report_path.write_text(
                json.dumps(page_report, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            print(f"\nPAGE {page_number} FINISHED")
            print(f"Detected lines: {len(lines)}")
            print(f"Combined text: {combined_path}")
            print(f"Detection overlay: {manifest.get('overlay_path')}")

    finally:
        pdf.close()

    report_path = OUTPUT_DIR / "reports" / "line_ocr_v1_report.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("\n" + "=" * 68)
    print("LINE-WISE OCR V1 FINISHED")
    print(f"Report: {report_path}")
    print(f"Output: {OUTPUT_DIR}")
    print("Every output requires visual review; no automatic correction or deletion.")
    print("=" * 68)


if __name__ == "__main__":
    main()
