import streamlit as st
from PIL import Image


def render_params(method, prefix: str, counter: int) -> dict:
    params = {}
    for spec in method.PARAMS:
        ptype = spec["type"]
        k = f"{prefix}_{spec.get('key', ptype)}_{counter}"

        if ptype == "channels":
            st.markdown("**Canaux :**")
            cols = st.columns(3)
            labels = ["R", "G", "B"]
            active = [
                cols[i].checkbox(labels[i], value=True, key=f"{prefix}_{labels[i].lower()}_{counter}")
                for i in range(3)
            ]
            params["channels"] = [l for l, a in zip(labels, active) if a]

        elif ptype == "slider":
            params[spec["key"]] = st.slider(
                spec["label"], spec["min"], spec["max"], spec["default"], key=k
            )

        elif ptype == "text":
            input_type = "password" if spec.get("password") else "default"
            params[spec["key"]] = st.text_input(
                spec["label"], value=spec.get("default", ""), type=input_type, key=k
            )

        elif ptype == "select":
            opts = spec["options"]
            params[spec["key"]] = st.selectbox(
                spec["label"], opts, index=opts.index(spec["default"]), key=k
            )

    return params


def show_capacity(method, image: Image.Image, params: dict) -> None:
    if hasattr(method, "capacity_info"):
        info = method.capacity_info(image, **params)
        if info:
            st.info(info)
