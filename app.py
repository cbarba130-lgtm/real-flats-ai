import streamlit as st
import cv2
import numpy as np
from io import BytesIO
from PIL import Image, ImageOps

APP_NAME = "Real Flats AI"
TAGLINE = "Turn sketches into editable fashion flats."

st.set_page_config(page_title=APP_NAME, layout="wide")

st.title(APP_NAME)
st.caption(TAGLINE)

st.markdown("""
**v0.5 Illustrator Prep Mode**  
This version stops trying to perfectly auto-vectorize.  
Instead, it creates clean Illustrator-ready prep files for faster tracing/redrawing.
""")

uploaded_file = st.file_uploader(
    "Upload a flat sketch",
    type=["jpg", "jpeg", "png", "tif", "tiff"]
)

with st.sidebar:
    st.header("Cleanup Settings")

    threshold_mode = st.radio("Threshold mode", ["Auto", "Manual"], index=0)

    manual_threshold = st.slider(
        "Manual threshold",
        0,
        255,
        170,
        disabled=(threshold_mode == "Auto")
    )

    remove_specks = st.slider(
        "Remove tiny specks smaller than",
        0,
        2000,
        80
    )

    line_boost = st.slider(
        "Line darkness boost",
        1.0,
        3.0,
        1.4,
        0.1
    )

    make_template_opacity = st.slider(
        "Template opacity",
        5,
        80,
        25
    )


def load_image(uploaded_bytes):
    image = Image.open(BytesIO(uploaded_bytes)).convert("RGB")
    return image


def pil_to_cv_gray(pil_img):
    arr = np.array(pil_img)
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    return gray


def clean_line_art(gray, threshold_mode, manual_threshold, remove_specks):
    blur = cv2.GaussianBlur(gray, (3, 3), 0)

    if threshold_mode == "Auto":
        _, bw = cv2.threshold(
            blur,
            0,
            255,
            cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
        )
    else:
        _, bw = cv2.threshold(
            blur,
            manual_threshold,
            255,
            cv2.THRESH_BINARY_INV
        )

    if remove_specks > 0:
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(bw, 8)
        cleaned = np.zeros_like(bw)

        for i in range(1, num_labels):
            area = stats[i, cv2.CC_STAT_AREA]
            if area >= remove_specks:
                cleaned[labels == i] = 255

        bw = cleaned

    # Convert back so black line art is black on white background
    clean = 255 - bw
    return clean


def boost_lines(gray, boost):
    arr = gray.astype(np.float32)
    arr = 255 - ((255 - arr) * boost)
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    return arr


def make_template(clean_img, opacity_percent):
    opacity = opacity_percent / 100.0

    # Light gray line art on white
    template = clean_img.astype(np.float32)
    template = 255 - ((255 - template) * opacity)
    template = np.clip(template, 0, 255).astype(np.uint8)

    return template


def png_bytes_from_array(arr):
    pil_img = Image.fromarray(arr).convert("RGB")
    out = BytesIO()
    pil_img.save(out, format="PNG")
    out.seek(0)
    return out.getvalue()


def make_svg_template(clean_img, opacity_percent):
    height, width = clean_img.shape

    # This SVG embeds the cleaned PNG as a tracing reference.
    png_data = png_bytes_from_array(clean_img)

    import base64
    encoded = base64.b64encode(png_data).decode("utf-8")

    opacity = opacity_percent / 100.0

    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     width="{width}"
     height="{height}"
     viewBox="0 0 {width} {height}">
  <g id="Locked_Template_Reference" opacity="{opacity}">
    <image href="data:image/png;base64,{encoded}"
           x="0"
           y="0"
           width="{width}"
           height="{height}" />
  </g>
  <g id="Redraw_Layer">
  </g>
</svg>
'''
    return svg.encode("utf-8")


if uploaded_file:
    file_bytes = uploaded_file.read()

    original = load_image(file_bytes)
    gray = pil_to_cv_gray(original)

    boosted = boost_lines(gray, line_boost)

    clean = clean_line_art(
        boosted,
        threshold_mode,
        manual_threshold,
        remove_specks
    )

    template = make_template(clean, make_template_opacity)

    clean_png = png_bytes_from_array(clean)
    template_png = png_bytes_from_array(template)
    svg_template = make_svg_template(clean, make_template_opacity)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("Original")
        st.image(original, use_column_width=True)

    with col2:
        st.subheader("Clean High-Contrast Art")
        st.image(clean, clamp=True, use_column_width=True)

    with col3:
        st.subheader("Light Gray Illustrator Template")
        st.image(template, clamp=True, use_column_width=True)

    st.divider()

    st.subheader("Downloads")

    st.download_button(
        "Download Clean PNG",
        data=clean_png,
        file_name="real_flats_ai_clean_art.png",
        mime="image/png"
    )

    st.download_button(
        "Download Light Gray Template PNG",
        data=template_png,
        file_name="real_flats_ai_template.png",
        mime="image/png"
    )

    st.download_button(
        "Download Illustrator Template SVG",
        data=svg_template,
        file_name="real_flats_ai_illustrator_template.svg",
        mime="image/svg+xml"
    )

    st.info(
        "Recommended Illustrator workflow: Open the template SVG, lock the reference layer, redraw on the Redraw_Layer, then save as .AI."
    )

else:
    st.info("Upload a clean CAD flat sketch to begin.")
