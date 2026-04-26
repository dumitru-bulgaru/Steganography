import numpy as np


def message_to_bits(message: str) -> np.ndarray:
    data = message.encode("utf-8")
    header = np.frombuffer(len(data).to_bytes(4, "big"), dtype=np.uint8)
    body = np.frombuffer(data, dtype=np.uint8)
    return np.unpackbits(np.concatenate([header, body]))


def bits_to_message(bits: np.ndarray) -> str:
    bits = np.asarray(bits, dtype=np.uint8)
    if len(bits) < 32:
        return ""
    length = int.from_bytes(np.packbits(bits[:32]).tobytes(), "big")
    if length == 0:
        return ""
    max_length = (len(bits) - 32) // 8
    if length > max_length:
        return (
            f"[Décodage échoué : l'en-tête indique {length} octets "
            f"mais seulement {max_length} disponibles — mauvais paramètres ?]"
        )
    return np.packbits(bits[32 : 32 + length * 8]).tobytes().decode("utf-8", errors="replace")
