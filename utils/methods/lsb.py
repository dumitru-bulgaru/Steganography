import io
import numpy as np
from PIL import Image
from utils.bit_utils import message_to_bits, bits_to_message

NAME = "LSB Séquentiel"
DESCRIPTION = (
    "Remplace les *n* bits de poids faible de chaque canal sélectionné "
    "en parcourant les pixels dans l'ordre séquentiel. "
    "Simple, grande capacité, mais détectable par analyse statistique."
)
PARAMS = [
    {"type": "channels"},
    {"type": "slider", "key": "n_bits", "label": "Bits par canal (n)", "min": 1, "max": 8, "default": 1},
]

_CH = {"R": 0, "G": 1, "B": 2}


def capacity_info(image: Image.Image, channels: list[str] = None, n_bits: int = 1, **_) -> str:
    ch = [_CH[c] for c in (channels or []) if c in _CH]
    if not ch:
        return "Sélectionnez au moins un canal."
    h, w = np.array(image).shape[:2]
    usable = max(0, h * w * len(ch) * n_bits // 8 - 4)
    return f"Capacité : **{usable:,} octets** ({h}×{w} px, {len(ch)} canal(aux), {n_bits} bit(s)/canal)"


def encode(image: Image.Image, message: str, channels: list[str] = None, n_bits: int = 1, **_) -> bytes:
    ch = [_CH[c] for c in (channels or []) if c in _CH]
    if not ch:
        raise ValueError("Sélectionnez au moins un canal.")

    arr = np.array(image.convert("RGB"), dtype=np.uint8)
    h, w, _ = arr.shape
    bits = message_to_bits(message)
    total_slots = h * w * len(ch)

    if len(bits) > total_slots * n_bits:
        raise ValueError(
            f"Message trop grand : {len(bits)} bits nécessaires, "
            f"{total_slots * n_bits} disponibles ({total_slots * n_bits // 8 - 4} octets utiles)."
        )

    bits_padded = np.pad(bits, (0, total_slots * n_bits - len(bits)))
    powers = (1 << np.arange(n_bits - 1, -1, -1)).astype(np.uint8)
    chunk_vals = (bits_padded.reshape(total_slots, n_bits) * powers).sum(axis=1).astype(np.uint8)

    mask = np.uint8((1 << n_bits) - 1)
    clear = np.uint8(0xFF - mask)
    flat = arr.reshape(h * w, 3).copy()
    for i, c in enumerate(ch):
        flat[:, c] = (flat[:, c] & clear) | chunk_vals.reshape(h * w, len(ch))[:, i]

    buf = io.BytesIO()
    Image.fromarray(flat.reshape(h, w, 3)).save(buf, format="PNG")
    return buf.getvalue()


def decode(file_bytes: bytes, channels: list[str] = None, n_bits: int = 1, **_) -> str:
    ch = [_CH[c] for c in (channels or []) if c in _CH]
    if not ch:
        return "[Aucun canal sélectionné.]"

    arr = np.array(Image.open(io.BytesIO(file_bytes)).convert("RGB"), dtype=np.uint8)
    h, w, _ = arr.shape
    mask = np.uint8((1 << n_bits) - 1)
    flat = arr.reshape(h * w, 3)

    extracted = np.stack([flat[:, c] & mask for c in ch], axis=1).flatten()
    powers = (1 << np.arange(n_bits - 1, -1, -1)).astype(np.uint8)
    bits = ((extracted[:, None] & powers) > 0).astype(np.uint8).flatten()
    return bits_to_message(bits)
