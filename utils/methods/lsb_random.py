import hashlib
import io
import numpy as np
from PIL import Image
from utils.bit_utils import message_to_bits, bits_to_message

NAME = "LSB Aléatoire (mot de passe)"
DESCRIPTION = (
    "Identique au LSB Séquentiel, mais les pixels sont sélectionnés selon une séquence "
    "pseudo-aléatoire initialisée par un mot de passe. "
    "Beaucoup plus résistant à l'analyse statistique : sans le mot de passe, "
    "les bits cachés sont indiscernables du bruit."
)
PARAMS = [
    {"type": "channels"},
    {"type": "slider", "key": "n_bits", "label": "Bits par canal (n)", "min": 1, "max": 8, "default": 1},
    {"type": "text", "key": "password", "label": "Mot de passe", "default": "", "password": True},
]

_CH = {"R": 0, "G": 1, "B": 2}


def _seed(password: str) -> np.random.SeedSequence:
    digest = hashlib.sha256(password.encode("utf-8")).digest()
    return np.random.SeedSequence(list(digest))


def capacity_info(image: Image.Image, channels: list[str] = None, n_bits: int = 1, **_) -> str:
    ch = [_CH[c] for c in (channels or []) if c in _CH]
    if not ch:
        return "Sélectionnez au moins un canal."
    h, w = np.array(image).shape[:2]
    usable = max(0, h * w * len(ch) * n_bits // 8 - 4)
    return f"Capacité : **{usable:,} octets** ({h}×{w} px, {len(ch)} canal(aux), {n_bits} bit(s)/canal)"


def _shuffled_slots(h: int, w: int, ch: list[int], password: str):
    """Returns (sel_y, sel_x, sel_c) arrays for all slots in shuffled order."""
    total = h * w * len(ch)
    pixel_idx = np.repeat(np.arange(h * w), len(ch))
    chan_idx = np.tile(np.array(ch), h * w)
    perm = np.random.default_rng(_seed(password)).permutation(total)
    pixel_idx = pixel_idx[perm]
    return pixel_idx // w, pixel_idx % w, chan_idx[perm]


def encode(image: Image.Image, message: str, channels: list[str] = None, n_bits: int = 1, password: str = "", **_) -> bytes:
    ch = [_CH[c] for c in (channels or []) if c in _CH]
    if not ch:
        raise ValueError("Sélectionnez au moins un canal.")
    if not password:
        raise ValueError("Un mot de passe est requis pour cette méthode.")

    arr = np.array(image.convert("RGB"), dtype=np.uint8)
    h, w, _ = arr.shape
    bits = message_to_bits(message)
    total_slots = h * w * len(ch)

    if len(bits) > total_slots * n_bits:
        raise ValueError(
            f"Message trop grand : {len(bits)} bits nécessaires, {total_slots * n_bits} disponibles."
        )

    bits_padded = np.pad(bits, (0, total_slots * n_bits - len(bits)))
    powers = (1 << np.arange(n_bits - 1, -1, -1)).astype(np.uint8)
    chunk_vals = (bits_padded.reshape(total_slots, n_bits) * powers).sum(axis=1).astype(np.uint8)

    mask = np.uint8((1 << n_bits) - 1)
    clear = np.uint8(0xFF - mask)
    sel_y, sel_x, sel_c = _shuffled_slots(h, w, ch, password)

    result = arr.copy()
    result[sel_y, sel_x, sel_c] = (result[sel_y, sel_x, sel_c] & clear) | chunk_vals

    buf = io.BytesIO()
    Image.fromarray(result).save(buf, format="PNG")
    return buf.getvalue()


def decode(file_bytes: bytes, channels: list[str] = None, n_bits: int = 1, password: str = "", **_) -> str:
    ch = [_CH[c] for c in (channels or []) if c in _CH]
    if not ch:
        return "[Aucun canal sélectionné.]"
    if not password:
        return "[Un mot de passe est requis pour cette méthode.]"

    arr = np.array(Image.open(io.BytesIO(file_bytes)).convert("RGB"), dtype=np.uint8)
    h, w, _ = arr.shape
    sel_y, sel_x, sel_c = _shuffled_slots(h, w, ch, password)

    mask = np.uint8((1 << n_bits) - 1)
    extracted = arr[sel_y, sel_x, sel_c] & mask
    powers = (1 << np.arange(n_bits - 1, -1, -1)).astype(np.uint8)
    bits = ((extracted[:, None] & powers) > 0).astype(np.uint8).flatten()
    return bits_to_message(bits)
