import uuid
from pathlib import Path
from PIL import Image

# utils/ sits one level below the project root; storage folders live under app/
BASE_DIR = Path(__file__).parent.parent / "app"

INPUT_ENCODE = BASE_DIR / "input_encode"
OUTPUT_ENCODE = BASE_DIR / "output_encode"
INPUT_DECODE = BASE_DIR / "input_decode"

_FOLDERS = [INPUT_ENCODE, OUTPUT_ENCODE, INPUT_DECODE]


def _ensure_dirs() -> None:
    for folder in _FOLDERS:
        folder.mkdir(exist_ok=True)


def save_image(image: Image.Image, folder: Path, prefix: str = "") -> Path:
    _ensure_dirs()
    path = folder / f"{prefix}{uuid.uuid4().hex[:10]}.png"
    image.save(path, format="PNG")
    return path
