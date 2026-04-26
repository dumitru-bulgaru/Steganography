import io
import numpy as np
from PIL import Image
from utils.bit_utils import message_to_bits, bits_to_message

NAME = "DCT par blocs"
DESCRIPTION = (
    "Découpe l'image en blocs 8×8 et modifie un coefficient DCT de fréquence moyenne "
    "dans chaque bloc via une modulation par indice de quantification (QIM). "
    "Résistant aux ajustements de luminosité et aux légères retouches. "
    "Capacité plus faible que LSB, mais distorsion concentrée sur les fréquences invisibles."
)
PARAMS = [
    {"type": "select", "key": "channel", "label": "Canal porteur", "options": ["R", "G", "B"], "default": "R"},
    {"type": "slider", "key": "strength", "label": "Pas de quantification (force)", "min": 2, "max": 50, "default": 10},
]

_CH = {"R": 0, "G": 1, "B": 2}
_BLOCK = 8
# Mid-frequency coefficient to modify (avoid DC=[0,0] and high-freq corners)
_COEFF_U, _COEFF_V = 4, 1

# Precompute orthonormal 8×8 DCT-II matrix (D @ D.T = I)
def _build_dct_matrix(N: int = 8) -> np.ndarray:
    k = np.arange(N)
    n = np.arange(N)
    D = np.cos(np.pi * np.outer(k, 2 * n + 1) / (2 * N))
    D[0] *= 1.0 / np.sqrt(N)
    D[1:] *= np.sqrt(2.0 / N)
    return D


_D = _build_dct_matrix(_BLOCK)
_DT = _D.T


def _dct2(block: np.ndarray) -> np.ndarray:
    return _D @ block.astype(float) @ _DT


def _idct2(block: np.ndarray) -> np.ndarray:
    return _DT @ block @ _D


def capacity_info(image: Image.Image = None, channel: str = "R", **_) -> str:
    if image is None:
        return ""
    h, w = np.array(image).shape[:2]
    n_blocks = (h // _BLOCK) * (w // _BLOCK)
    usable = max(0, n_blocks // 8 - 4)
    return (
        f"Capacité : **{usable:,} octets** "
        f"({(h // _BLOCK) * (w // _BLOCK)} blocs 8×8 sur le canal {channel})"
    )


def _embed_bit(coeff: float, bit: int, step: float) -> float:
    q = int(np.round(coeff / step))
    if q % 2 != bit:
        q = q + 1 if coeff >= q * step else q - 1
    return float(q * step)


def encode(image: Image.Image, message: str, channel: str = "R", strength: int = 10, **_) -> bytes:
    c = _CH.get(channel, 0)
    arr = np.array(image.convert("RGB"), dtype=np.uint8)
    h, w, _ = arr.shape

    bh, bw = h // _BLOCK, w // _BLOCK
    bits = message_to_bits(message)
    n_blocks = bh * bw

    if len(bits) > n_blocks:
        raise ValueError(
            f"Message trop grand : {len(bits)} bits nécessaires, "
            f"{n_blocks} blocs disponibles ({n_blocks // 8 - 4} octets utiles)."
        )

    result = arr.copy().astype(float)
    bit_idx = 0

    for by in range(bh):
        for bx in range(bw):
            y0, x0 = by * _BLOCK, bx * _BLOCK
            block = result[y0 : y0 + _BLOCK, x0 : x0 + _BLOCK, c]
            coeffs = _dct2(block)
            if bit_idx < len(bits):
                coeffs[_COEFF_U, _COEFF_V] = _embed_bit(coeffs[_COEFF_U, _COEFF_V], int(bits[bit_idx]), strength)
                bit_idx += 1
            result[y0 : y0 + _BLOCK, x0 : x0 + _BLOCK, c] = np.clip(np.round(_idct2(coeffs)), 0, 255)

    buf = io.BytesIO()
    Image.fromarray(result.astype(np.uint8)).save(buf, format="PNG")
    return buf.getvalue()


def decode(file_bytes: bytes, channel: str = "R", strength: int = 10, **_) -> str:
    c = _CH.get(channel, 0)
    arr = np.array(Image.open(io.BytesIO(file_bytes)).convert("RGB"), dtype=np.uint8)
    h, w, _ = arr.shape

    bh, bw = h // _BLOCK, w // _BLOCK
    bits = []

    for by in range(bh):
        for bx in range(bw):
            y0, x0 = by * _BLOCK, bx * _BLOCK
            block = arr[y0 : y0 + _BLOCK, x0 : x0 + _BLOCK, c]
            coeffs = _dct2(block)
            q = int(np.round(coeffs[_COEFF_U, _COEFF_V] / strength))
            bits.append(q % 2)

    return bits_to_message(np.array(bits, dtype=np.uint8))
