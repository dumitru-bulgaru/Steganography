import sys
from pathlib import Path

import streamlit as st
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent.parent))  # project root
sys.path.insert(0, str(Path(__file__).parent.parent))          # app/

from utils.methods import REGISTRY, METHOD_NAMES
from utils.files import save_image, INPUT_DECODE
from ui import render_params

st.set_page_config(page_title="Décoder", page_icon="🔓", layout="centered")

# ── session state ─────────────────────────────────────────────────────────────

for key, default in [("dec_counter", 0), ("dec_result", None)]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── header ────────────────────────────────────────────────────────────────────

col_title, col_clear = st.columns([5, 1])
col_title.title("Décoder")
if col_clear.button("Effacer", use_container_width=True):
    st.session_state.dec_counter += 1
    st.session_state.dec_result = None
    st.rerun()

counter = st.session_state.dec_counter

# ── method selector ───────────────────────────────────────────────────────────

method_name = st.selectbox("Méthode de stéganographie", METHOD_NAMES, key=f"dec_method_{counter}")
method = REGISTRY[method_name]
st.caption(method.DESCRIPTION)
st.divider()

# ── inputs ────────────────────────────────────────────────────────────────────

uploaded = st.file_uploader("Image PNG (stégo)", type=["png"], key=f"dec_upload_{counter}")

if uploaded:
    image = Image.open(uploaded)
    w, h = image.size
    st.image(uploaded, caption=f"{w}×{h} px", use_container_width=True)

st.markdown("---")
params = render_params(method, "dec", counter)
st.caption("Utilisez exactement les mêmes paramètres qu'à l'encodage.")

# ── decode ────────────────────────────────────────────────────────────────────

if st.button("Décoder", type="primary", key=f"dec_btn_{counter}"):
    if not uploaded:
        st.error("Veuillez uploader une image PNG.")
    else:
        try:
            file_bytes = uploaded.getvalue()
            save_image(Image.open(uploaded), INPUT_DECODE, prefix="input_")
            st.session_state.dec_result = method.decode(file_bytes, **params)
            st.rerun()
        except Exception as exc:
            st.error(f"Erreur inattendue : {exc}")

# ── result ────────────────────────────────────────────────────────────────────

if st.session_state.dec_result is not None:
    st.divider()
    st.subheader("Message extrait")
    st.text_area("", value=st.session_state.dec_result, height=200, key="dec_output")
