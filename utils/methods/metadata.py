import io
from PIL import Image, PngImagePlugin

NAME = "Métadonnées tEXt"
DESCRIPTION = (
    "Stocke le message dans un chunk de métadonnées texte (tEXt/iTXt) du fichier PNG. "
    "Zéro dégradation visuelle. "
    "Visible dans les propriétés du fichier ou avec ExifTool — peu discret, mais pratique."
)
PARAMS = [
    {"type": "text", "key": "key_name", "label": "Clé de métadonnée", "default": "Comment"},
]


def capacity_info(image: Image.Image = None, **_) -> str:
    return "Capacité : **illimitée** (données stockées dans les métadonnées, pas dans les pixels)"


def encode(image: Image.Image, message: str, key_name: str = "Comment", **_) -> bytes:
    info = PngImagePlugin.PngInfo()
    info.add_itxt(key_name, message, lang="", tkey="")
    buf = io.BytesIO()
    image.convert("RGB").save(buf, format="PNG", pnginfo=info)
    return buf.getvalue()


def decode(file_bytes: bytes, key_name: str = "Comment", **_) -> str:
    img = Image.open(io.BytesIO(file_bytes))
    # PIL exposes tEXt as .text and iTXt as .text (merged dict)
    text_data = getattr(img, "text", {})
    if key_name in text_data:
        return text_data[key_name]
    return f"[Aucune métadonnée trouvée pour la clé '{key_name}'.]"
