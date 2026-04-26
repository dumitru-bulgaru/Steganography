from utils.methods import lsb, lsb_random, png_chunk, metadata, dct

REGISTRY: dict = {
    lsb.NAME: lsb,
    lsb_random.NAME: lsb_random,
    png_chunk.NAME: png_chunk,
    metadata.NAME: metadata,
    dct.NAME: dct,
}

METHOD_NAMES: list[str] = list(REGISTRY.keys())
