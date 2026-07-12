from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DB_PATH = PROJECT_ROOT / "sams.db"
OUTPUT_DIR = PROJECT_ROOT / "output"
REFERENCES_DIR = PROJECT_ROOT / "references"

SUPPORTED_IMAGE_EXTENSIONS = (".png", ".jpeg", ".jpg")
