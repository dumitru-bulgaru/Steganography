import io
import struct
import zlib
from PIL import Image

NAME = "Chunk PNG personnalisé"
DESCRIPTION = (
    "Injecte le message dans un chunk ancillaire personnalisé du fichier PNG. "
    "Zéro dégradation visuelle — les pixels ne sont pas modifiés. "
    "Indétectable visuellement, mais visible avec un éditeur hexadécimal ou un outil PNG."
)
PARAMS = [
    {"type": "text", "key": "chunk_name", "label": "Nom du chunk (4 caractères)", "default": "stGo"},
]

_PNG_SIG = b"\x89PNG\r\n\x1a\n"


def capacity_info(image: Image.Image = None, **_) -> str:
    return "Capacité : **illimitée** (données stockées dans le fichier, pas dans les pixels)"


def _make_chunk(name: bytes, data: bytes) -> bytes:
    crc = zlib.crc32(name + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + name + data + struct.pack(">I", crc)


def _iter_chunks(png_bytes: bytes):
    pos = 8  # skip signature
    while pos + 8 <= len(png_bytes):
        length = struct.unpack(">I", png_bytes[pos : pos + 4])[0]
        name = png_bytes[pos + 4 : pos + 8]
        data = png_bytes[pos + 8 : pos + 8 + length]
        yield name, data, pos
        pos += 12 + length


def encode(image: Image.Image, message: str, chunk_name: str = "stGo", **_) -> bytes:
    name = chunk_name[:4].ljust(4).encode("ascii")
    if not name[0:1].islower():
        # PNG spec: ancillary chunks must start with a lowercase letter
        name = bytes([name[0] | 0x20]) + name[1:]

    buf = io.BytesIO()
    image.convert("RGB").save(buf, format="PNG")
    png_bytes = buf.getvalue()

    iend_pos = next(pos for cname, _, pos in _iter_chunks(png_bytes) if cname == b"IEND")
    custom = _make_chunk(name, message.encode("utf-8"))
    return png_bytes[:iend_pos] + custom + png_bytes[iend_pos:]


def decode(file_bytes: bytes, chunk_name: str = "stGo", **_) -> str:
    name = chunk_name[:4].ljust(4).encode("ascii")
    if not name[0:1].islower():
        name = bytes([name[0] | 0x20]) + name[1:]

    for cname, data, _ in _iter_chunks(file_bytes):
        if cname == name:
            return data.decode("utf-8", errors="replace")

    return f"[Aucun chunk '{chunk_name}' trouvé dans ce fichier PNG.]"
