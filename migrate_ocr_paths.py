from pathlib import Path
import re
import shutil
import sys

ROOT = Path.cwd().resolve()
SCRIPTS = ROOT / "research" / "ocr" / "scripts"
CONFIG = ROOT / "research" / "ocr" / "config"
BACKUP = ROOT / "ocr-organization-backup" / "scripts_before_path_migration"

FILES = [
"audits/mizan_pdf_quality_audit.py",
"benchmarks/mizan_arabic_accuracy_benchmark_v1.py",
"benchmarks/mizan_arabic_accuracy_benchmark_v2.py",
"detection/mizan_detect_lines.py",
"detection/mizan_detect_lines_gpu.py",
"grouping/mizan_grouping_preview.py",
"grouping/mizan_grouping_preview_v2.py",
"grouping/mizan_grouping_v3_arabic_test.py",
"pipelines/mizan_line_ocr_v1.py",
"preprocessing/mizan_arabic_clahe_padding_benchmark_v1.py",
"preprocessing/mizan_arabic_contrast_benchmark_v1.py",
"preprocessing/mizan_arabic_enhancement_benchmark_v1.py",
"qari/mizan_qari_crop_test.py",
"qari/mizan_qari_paragraph_test.py",
"qari/qari_benchmark.py",
"qari/qari_test.py",
"qari/tiled/qari_tiled_ocr.py",
"qari/tiled/qari_tiled_ocr_v2.py",
"qari/tiled/qari_tiled_ocr_v3.py",
"qari/tiled/qari_tiled_ocr_v4.py",
]

PATHS = """from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
OCR_ROOT = PROJECT_ROOT / "research" / "ocr"
CONFIG_DIR = OCR_ROOT / "config"
SCRIPTS_DIR = OCR_ROOT / "scripts"
DATASETS_DIR = OCR_ROOT / "datasets"
TEST_IMAGES_DIR = DATASETS_DIR / "test_images"
RESULTS_DIR = OCR_ROOT / "results"
DOCS_DIR = OCR_ROOT / "docs"
OCR_VENV_PYTHON = PROJECT_ROOT / "ocr-venv" / "Scripts" / "python.exe"
QARI_VENV_PYTHON = PROJECT_ROOT / "qari-venv" / "Scripts" / "python.exe"
BOOKS_DIR = PROJECT_ROOT / "data" / "books"
IHYA_VOL1_PDF = BOOKS_DIR / "tasawwuf" / "ihya_ulum_al_din" / "Imam abu Hamid al-Ghazali - Ulum al-Din - Revivication of the Islamic Sciences - vol 1 of 4 (2011, Dar ul-Kutub al-Ilmiyah).pdf"
BENCHMARK_RESULTS_DIR = RESULTS_DIR / "benchmarks"
DETECTION_RESULTS_DIR = RESULTS_DIR / "detection"
QARI_RESULTS_DIR = RESULTS_DIR / "qari"
PREPROCESSING_RESULTS_DIR = RESULTS_DIR / "preprocessing"
DETECTION_GPU_DIR = DETECTION_RESULTS_DIR / "gpu_detection_test"
GROUPING_RESULTS_DIR = QARI_RESULTS_DIR / "grouping"
GROUPING_PREVIEW_DIR = GROUPING_RESULTS_DIR / "qari_grouping_preview"
GROUPING_PREVIEW_V2_DIR = GROUPING_RESULTS_DIR / "qari_grouping_preview_v2"
GROUPING_V3_DIR = GROUPING_RESULTS_DIR / "qari_grouping_v3_arabic_test"
QARI_CROP_DIR = QARI_RESULTS_DIR / "crop" / "qari_crop_test"
QARI_PARAGRAPH_DIR = QARI_RESULTS_DIR / "paragraph" / "qari_paragraph_test"
QARI_TEST_DIR = QARI_RESULTS_DIR / "paragraph" / "qari_test"
QARI_BENCHMARK_DIR = BENCHMARK_RESULTS_DIR / "qari_benchmark"
ACCURACY_BENCHMARK_V1_DIR = BENCHMARK_RESULTS_DIR / "arabic_accuracy_benchmark_v1"
ACCURACY_BENCHMARK_V2_DIR = BENCHMARK_RESULTS_DIR / "arabic_accuracy_benchmark_v2"
CLAHE_PADDING_BENCHMARK_DIR = BENCHMARK_RESULTS_DIR / "arabic_clahe_padding_benchmark_v1"
CONTRAST_BENCHMARK_DIR = BENCHMARK_RESULTS_DIR / "arabic_contrast_benchmark_v1"
ENHANCEMENT_BENCHMARK_DIR = BENCHMARK_RESULTS_DIR / "arabic_enhancement_benchmark_v1"
TILED_V1_DIR = QARI_RESULTS_DIR / "tiled" / "qari_tiled_results"
TILED_V2_DIR = QARI_RESULTS_DIR / "tiled" / "qari_tiled_v2_results"
TILED_V3_DIR = QARI_RESULTS_DIR / "tiled" / "qari_tiled_v3_results"
TILED_V4_DIR = QARI_RESULTS_DIR / "tiled" / "qari_tiled_v4_results"
PIPELINE_RESULTS_DIR = RESULTS_DIR / "pipelines"
LINE_OCR_V1_DIR = PIPELINE_RESULTS_DIR / "mizan_line_ocr_v1"
AUDIT_RESULTS_DIR = RESULTS_DIR / "audits"
"""

BOOTSTRAP = "\n".join([
    "# Shared Mizan OCR paths",
    "import sys as _sys",
    "from pathlib import Path as _Path",
    "for _parent in _Path(__file__).resolve().parents:",
    '    if (_parent / "research" / "ocr" / "config" / "paths.py").is_file():',
    "        _sys.path.insert(0, str(_parent))",
    "        break",
    "else:",
    '    raise RuntimeError("Cannot locate Mizan project root.")',
    "from research.ocr.config.paths import *",
    ""
])

def add_import(src):
    if "from research.ocr.config.paths import *" in src:
        return src
    future = re.search(r"^from __future__ import .+$", src, re.M)
    if future:
        pos = future.end()
        return src[:pos] + "\n\n" + BOOTSTRAP + src[pos:]
    doc = re.match(r'\A\s*(?P<q>"""|\'\'\')[\s\S]*?(?P=q)', src)
    if doc:
        pos = doc.end()
        return src[:pos] + "\n\n" + BOOTSTRAP + src[pos:]
    return BOOTSTRAP + "\n" + src

def replace(src, pattern, repl, label):
    result, count = re.subn(pattern, repl, src, count=1, flags=re.M | re.S)
    if count != 1:
        raise RuntimeError(f"{label}: expected one match, got {count}")
    return result

def patch(rel, src):
    src = add_import(src)
    if rel == "audits/mizan_pdf_quality_audit.py":
        src = replace(src, r"ROOT = Path\(__file__\)\.resolve\(\)\.parent\nBOOKS = ROOT / 'data' / 'books'\nOUT = ROOT / 'data' / 'processing_reports'", "ROOT = PROJECT_ROOT\nBOOKS = BOOKS_DIR\nOUT = AUDIT_RESULTS_DIR", rel)
    elif rel.endswith("accuracy_benchmark_v1.py"):
        src = replace(src, r'ROOT = Path\(__file__\)\.resolve\(\)\.parent\nINPUT_DIR = ROOT / "arabic_accuracy_benchmark_v1" / "input_crops"\nOUTPUT_DIR = ROOT / "arabic_accuracy_benchmark_v1"', 'ROOT = PROJECT_ROOT\nOUTPUT_DIR = ACCURACY_BENCHMARK_V1_DIR\nINPUT_DIR = OUTPUT_DIR / "input_crops"', rel)
    elif rel.endswith("accuracy_benchmark_v2.py"):
        src = replace(src, r'ROOT = Path\(__file__\)\.resolve\(\)\.parent\nBASE_DIR = ROOT / "arabic_accuracy_benchmark_v2"', 'ROOT = PROJECT_ROOT\nBASE_DIR = ACCURACY_BENCHMARK_V2_DIR', rel)
    elif rel == "detection/mizan_detect_lines_gpu.py":
        src = replace(src, r'BASE_DIR = Path\(__file__\)\.resolve\(\)\.parent\n\nDEFAULT_PDF = \([\s\S]*?\)\n\nDEFAULT_OUTPUT = BASE_DIR / "gpu_detection_test"', 'BASE_DIR = PROJECT_ROOT\nDEFAULT_PDF = IHYA_VOL1_PDF\nDEFAULT_OUTPUT = DETECTION_GPU_DIR', rel)
    elif rel == "grouping/mizan_grouping_preview.py":
        src = replace(src, r'BASE = Path\(__file__\)\.resolve\(\)\.parent\nDEFAULT_MANIFEST = BASE / "gpu_detection_test" / "line_manifest\.json"', 'BASE = PROJECT_ROOT\nDEFAULT_MANIFEST = DETECTION_GPU_DIR / "line_manifest.json"', rel)
        src = src.replace('default=BASE / "qari_grouping_preview"', 'default=GROUPING_PREVIEW_DIR')
    elif rel == "grouping/mizan_grouping_preview_v2.py":
        src = replace(src, r'BASE = Path\(__file__\)\.resolve\(\)\.parent\nDEFAULT = BASE / "gpu_detection_test" / "line_manifest\.json"', 'BASE = PROJECT_ROOT\nDEFAULT = DETECTION_GPU_DIR / "line_manifest.json"', rel)
        src = src.replace('default=BASE / "qari_grouping_preview_v2"', 'default=GROUPING_PREVIEW_V2_DIR')
    elif rel == "grouping/mizan_grouping_v3_arabic_test.py":
        src = replace(src, r'BASE = Path\(__file__\)\.resolve\(\)\.parent\nDEFAULT_MANIFEST = BASE / "gpu_detection_test" / "line_manifest\.json"', 'BASE = PROJECT_ROOT\nDEFAULT_MANIFEST = DETECTION_GPU_DIR / "line_manifest.json"', rel)
        src = src.replace('default=BASE/"qari_grouping_v3_arabic_test"', 'default=GROUPING_V3_DIR')
    elif rel == "pipelines/mizan_line_ocr_v1.py":
        src = replace(src, r'BASE_DIR = Path\(__file__\)\.resolve\(\)\.parent\n\nPDF_PATH = \([\s\S]*?\)\n\nOCR_PYTHON = BASE_DIR / "ocr-venv" / "Scripts" / "python\.exe"\nDETECTOR_SCRIPT = BASE_DIR / "mizan_detect_lines\.py"\n\nOUTPUT_DIR = BASE_DIR / "mizan_line_ocr_v1"', 'BASE_DIR = PROJECT_ROOT\nPDF_PATH = IHYA_VOL1_PDF\nOCR_PYTHON = OCR_VENV_PYTHON\nDETECTOR_SCRIPT = SCRIPTS_DIR / "detection" / "mizan_detect_lines.py"\nOUTPUT_DIR = LINE_OCR_V1_DIR', rel)
    elif rel.startswith("preprocessing/"):
        choices = {
          "preprocessing/mizan_arabic_clahe_padding_benchmark_v1.py": ("arabic_clahe_padding_benchmark_v1","CLAHE_PADDING_BENCHMARK_DIR"),
          "preprocessing/mizan_arabic_contrast_benchmark_v1.py": ("arabic_contrast_benchmark_v1","CONTRAST_BENCHMARK_DIR"),
          "preprocessing/mizan_arabic_enhancement_benchmark_v1.py": ("arabic_enhancement_benchmark_v1","ENHANCEMENT_BENCHMARK_DIR")}
        old, new = choices[rel]
        src = replace(src, r'BASE_DIR = Path\(__file__\)\.resolve\(\)\.parent\nDEFAULT_GROUP_DIR = BASE_DIR / "qari_grouping_v3_arabic_test" / "groups"', 'BASE_DIR = PROJECT_ROOT\nDEFAULT_GROUP_DIR = GROUPING_V3_DIR / "groups"', rel)
        src = src.replace(f'default=BASE_DIR / "{old}"', f'default={new}')
    elif rel in ("qari/mizan_qari_crop_test.py","qari/mizan_qari_paragraph_test.py"):
        src = replace(src, r'BASE_DIR = Path\(__file__\)\.resolve\(\)\.parent\nDEFAULT_MANIFEST = BASE_DIR / "gpu_detection_test" / "line_manifest\.json"', 'BASE_DIR = PROJECT_ROOT\nDEFAULT_MANIFEST = DETECTION_GPU_DIR / "line_manifest.json"', rel)
        if rel.endswith("crop_test.py"):
            src = src.replace('default=BASE_DIR / "qari_crop_test"', 'default=QARI_CROP_DIR')
        else:
            src = src.replace('default=BASE_DIR / "qari_paragraph_test"', 'default=QARI_PARAGRAPH_DIR')
    elif rel == "qari/qari_benchmark.py":
        src = replace(src, r'PDF_PATH = Path\(\s*r"C:\\Users\\kamra\\OneDrive\\Documents\\Mizan-Al-Tahqiq\\data\\books\\tasawwuf\\ihya_ulum_al_din\\Imam abu Hamid al-Ghazali - Ulum al-Din - Revivication of the Islamic Sciences - vol 1 of 4 \(2011, Dar ul-Kutub al-Ilmiyah\)\.pdf"\s*\)', 'PDF_PATH = IHYA_VOL1_PDF', rel)
        src = src.replace('BASE_DIR = Path(__file__).resolve().parent', 'BASE_DIR = PROJECT_ROOT')
        src = src.replace('OUTPUT_DIR = BASE_DIR / "qari_benchmark"', 'OUTPUT_DIR = QARI_BENCHMARK_DIR')
    elif rel == "qari/qari_test.py":
        src = replace(src, r'PDF_PATH = Path\(\s*r"C:\\Users\\kamra\\OneDrive\\Documents\\Mizan-Al-Tahqiq\\data\\books\\tasawwuf\\ihya_ulum_al_din\\Imam abu Hamid al-Ghazali - Ulum al-Din - Revivication of the Islamic Sciences - vol 1 of 4 \(2011, Dar ul-Kutub al-Ilmiyah\)\.pdf"\s*\)', 'PDF_PATH = IHYA_VOL1_PDF', rel)
        src = src.replace('OUTPUT_DIR = Path("qari_test")', 'OUTPUT_DIR = QARI_TEST_DIR')
    elif rel == "qari/tiled/qari_tiled_ocr.py":
        src = replace(src, r'PDF_PATH = Path\(\s*r"C:\\Users\\kamra\\OneDrive\\Documents\\Mizan-Al-Tahqiq\\data\\books\\tasawwuf\\ihya_ulum_al_din\\Imam abu Hamid al-Ghazali - Ulum al-Din - Revivication of the Islamic Sciences - vol 1 of 4 \(2011, Dar ul-Kutub al-Ilmiyah\)\.pdf"\s*\)', 'PDF_PATH = IHYA_VOL1_PDF', rel)
        src = src.replace('BASE_DIR = Path(__file__).resolve().parent', 'BASE_DIR = PROJECT_ROOT')
        src = src.replace('OUTPUT_DIR = BASE_DIR / "qari_tiled_results"', 'OUTPUT_DIR = TILED_V1_DIR')
    elif rel in ("qari/tiled/qari_tiled_ocr_v2.py","qari/tiled/qari_tiled_ocr_v3.py","qari/tiled/qari_tiled_ocr_v4.py"):
        version = rel.rsplit("_v",1)[1].split(".")[0]
        src = replace(src, r'BASE_DIR = Path\(__file__\)\.resolve\(\)\.parent\n\nPDF_PATH = \([\s\S]*?\)\n\nOUTPUT_DIR = BASE_DIR / "qari_tiled_v[234]_results"', f'BASE_DIR = PROJECT_ROOT\nPDF_PATH = IHYA_VOL1_PDF\nOUTPUT_DIR = TILED_V{version}_DIR', rel)
    return src

def main():
    if not (ROOT / "manage.py").is_file() or not SCRIPTS.is_dir():
        sys.exit("Run this from the Mizan-Al-Tahqiq project root.")
    missing = [f for f in FILES if not (SCRIPTS / f).is_file()]
    if missing:
        sys.exit("Missing expected files:\n" + "\n".join(missing))

    # Validate every transformation in memory before changing any file.
    updates = {}
    for rel in FILES:
        path = SCRIPTS / rel
        original = path.read_text(encoding="utf-8-sig")
        updated = patch(rel, original)
        if updated == original:
            raise RuntimeError(f"No update produced for {rel}")
        compile(updated, str(path), "exec")
        updates[rel] = updated

    CONFIG.mkdir(parents=True, exist_ok=True)
    for rel in FILES:
        src = SCRIPTS / rel
        dst = BACKUP / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists():
            shutil.copy2(src, dst)

    (CONFIG / "paths.py").write_text(PATHS, encoding="utf-8")
    (CONFIG / "bootstrap.py").write_text(
        "import sys\nfrom pathlib import Path\n"
        "PROJECT_ROOT = Path(__file__).resolve().parents[3]\n"
        "if str(PROJECT_ROOT) not in sys.path:\n    sys.path.insert(0, str(PROJECT_ROOT))\n"
        "from research.ocr.config.paths import *\n",
        encoding="utf-8"
    )
    for rel, updated in updates.items():
        (SCRIPTS / rel).write_text(updated, encoding="utf-8")

    print(f"SUCCESS: {len(updates)} scripts migrated.")
    print(f"Original script backups: {BACKUP}")
    print("No PDF, dataset, model or existing result folder was moved/deleted.")
    print("Next: python -m compileall research/ocr/scripts -q")

if __name__ == "__main__":
    main()
