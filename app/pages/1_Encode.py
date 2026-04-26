import io
import sys
from pathlib import Path

import streamlit as st
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent.parent))  # project root
sys.path.insert(0, str(Path(__file__).parent.parent))          # app/

from utils.methods import REGISTRY, METHOD_NAMES
from utils.files import save_image, INPUT_ENCODE, OUTPUT_ENCODE
from ui import render_params, show_capacity

st.set_page_config(page_title="Encoder", page_icon="🔒", layout="centered")

# ── session state ─────────────────────────────────────────────────────────────

for key, default in [("enc_counter", 0), ("enc_result_bytes", None), ("enc_result_name", "stego.png")]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── header ────────────────────────────────────────────────────────────────────

col_title, col_clear = st.columns([5, 1])
col_title.title("Encoder")
if col_clear.button("Effacer", use_container_width=True):
    st.session_state.enc_counter += 1
    st.session_state.enc_result_bytes = None
    st.rerun()

counter = st.session_state.enc_counter

# ── method selector ───────────────────────────────────────────────────────────

method_name = st.selectbox("Méthode de stéganographie", METHOD_NAMES, key=f"enc_method_{counter}")
method = REGISTRY[method_name]
st.caption(method.DESCRIPTION)
st.divider()

# ── inputs ────────────────────────────────────────────────────────────────────

uploaded = st.file_uploader("Image PNG", type=["png"], key=f"enc_upload_{counter}")
message = st.text_area(
    "Message secret",
    height=120,
    placeholder="Écrivez le message à cacher…",
    key=f"enc_message_{counter}",
)

st.markdown("---")
params = render_params(method, "enc", counter)

# ── capacity hint ─────────────────────────────────────────────────────────────

if uploaded:
    image = Image.open(uploaded)
    show_capacity(method, image, params)
    if message:
        st.caption(f"Taille du message : **{len(message.encode('utf-8')):,} octets**")

# ── encode ────────────────────────────────────────────────────────────────────

if st.button("Encoder", type="primary", key=f"enc_btn_{counter}"):
    if not uploaded:
        st.error("Veuillez uploader une image PNG.")
    elif not message.strip():
        st.error("Veuillez saisir un message.")
    else:
        try:
            image = Image.open(uploaded)
            result_bytes = method.encode(image, message, **params)

            save_image(image, INPUT_ENCODE, prefix="input_")
            out_path = save_image(Image.open(io.BytesIO(result_bytes)), OUTPUT_ENCODE, prefix="stego_")

            st.session_state.enc_result_bytes = result_bytes
            st.session_state.enc_result_name = out_path.name
            st.success("Message encodé avec succès.")
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))
        except Exception as exc:
            st.error(f"Erreur inattendue : {exc}")

# ── result ────────────────────────────────────────────────────────────────────

if st.session_state.enc_result_bytes:
    st.divider()
    st.subheader("Résultat")

    if uploaded:
        col_orig, col_stego = st.columns(2)
        col_orig.image(uploaded, caption="Original", use_container_width=True)
        col_stego.image(
            st.session_state.enc_result_bytes,
            caption="Stégo (visuellement identique)",
            use_container_width=True,
        )
    else:
        st.image(st.session_state.enc_result_bytes, caption="Image stégo", use_container_width=True)

    st.download_button(
        "Télécharger l'image stégo",
        data=st.session_state.enc_result_bytes,
        file_name=st.session_state.enc_result_name,
        mime="image/png",
        use_container_width=True,
    )
