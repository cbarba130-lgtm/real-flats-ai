import streamlit as st
import svgwrite
from io import StringIO

APP_NAME = "Real Flats AI"
TAGLINE = "Turn sketches into editable fashion flats."

st.set_page_config(page_title=APP_NAME, layout="wide")

st.title(APP_NAME)
st.caption(TAGLINE)

st.markdown("""
**Dress Generator v1**  
This version builds clean editable vector flats from garment choices instead of tracing pixels.
""")

with st.sidebar:
    st.header("Dress Options")

    dress_type = st.selectbox(
        "Dress type",
        ["Shift Dress", "Fit & Flare Dress", "Tee Dress"]
    )

    neckline = st.selectbox(
        "Neckline",
        ["Crew Neck", "V-Neck", "Square Neck"]
    )

    sleeve = st.selectbox(
        "Sleeve",
        ["Sleeveless", "Short Sleeve"]
    )

    waist_seam = st.checkbox("Waist seam", value=True)
    center_front_seam = st.checkbox("Center front seam", value=False)
    center_back_seam = st.checkbox("Center back seam", value=True)
    hem_stitch = st.checkbox("Hem stitch", value=True)
    back_zipper = st.checkbox("Back zipper", value=True)

    st.divider()

    outer_stroke = st.slider("Outer line weight", 0.5, 3.0, 1.5, 0.1)
    seam_stroke = st.slider("Seam line weight", 0.25, 2.0, 0.8, 0.05)
    stitch_stroke = st.slider("Stitch line weight", 0.25, 1.5, 0.5, 0.05)


def add_path(dwg, group, d, stroke_width=1, dasharray=None):
    attrs = {
        "d": d,
        "fill": "none",
        "stroke": "black",
        "stroke_width": stroke_width,
        "stroke_linecap": "round",
        "stroke_linejoin": "round"
    }

    if dasharray:
        attrs["stroke_dasharray"] = dasharray

    group.add(dwg.path(**attrs))


def draw_neckline(dwg, group, x, y, neckline, stroke):
    if neckline == "Crew Neck":
        add_path(
            dwg,
            group,
            f"M {x-28} {y} C {x-18} {y+18}, {x+18} {y+18}, {x+28} {y}",
            stroke
        )

    elif neckline == "V-Neck":
        add_path(
            dwg,
            group,
            f"M {x-30} {y} L {x} {y+42} L {x+30} {y}",
            stroke
        )

    elif neckline == "Square Neck":
        add_path(
            dwg,
            group,
            f"M {x-32} {y} L {x-32} {y+32} L {x+32} {y+32} L {x+32} {y}",
            stroke
        )


def draw_dress(dwg, group, x, y, view, dress_type, neckline, sleeve,
               waist_seam, center_seam, hem_stitch, zipper,
               outer_stroke, seam_stroke, stitch_stroke):

    top_y = y
    shoulder_y = y + 28
    armhole_y = y + 105
    waist_y = y + 210
    hem_y = y + 475

    if dress_type == "Shift Dress":
        bust_w = 92
        waist_w = 100
        hem_w = 145

    elif dress_type == "Fit & Flare Dress":
        bust_w = 88
        waist_w = 76
        hem_w = 165

    else:  # Tee Dress
        bust_w = 105
        waist_w = 110
        hem_w = 155

    # Body outer shape
    left_shoulder = x - bust_w / 2
    right_shoulder = x + bust_w / 2
    left_waist = x - waist_w / 2
    right_waist = x + waist_w / 2
    left_hem = x - hem_w / 2
    right_hem = x + hem_w / 2

    body_path = (
        f"M {left_shoulder} {shoulder_y} "
        f"C {left_shoulder-18} {armhole_y-35}, {left_waist-10} {waist_y-20}, {left_waist} {waist_y} "
        f"L {left_hem} {hem_y} "
        f"C {x-50} {hem_y+12}, {x+50} {hem_y+12}, {right_hem} {hem_y} "
        f"L {right_waist} {waist_y} "
        f"C {right_waist+10} {waist_y-20}, {right_shoulder+18} {armhole_y-35}, {right_shoulder} {shoulder_y}"
    )

    add_path(dwg, group, body_path, outer_stroke)

    # Shoulders
    add_path(
        dwg,
        group,
        f"M {left_shoulder} {shoulder_y} C {x-35} {top_y-5}, {x+35} {top_y-5}, {right_shoulder} {shoulder_y}",
        outer_stroke
    )

    # Neckline
    draw_neckline(dwg, group, x, top_y + 18, neckline, outer_stroke)

    # Sleeves
    if sleeve == "Short Sleeve":
        add_path(
            dwg,
            group,
            f"M {left_shoulder} {shoulder_y} L {left_shoulder-45} {shoulder_y+35} L {left_shoulder-18} {armhole_y}",
            outer_stroke
        )

        add_path(
            dwg,
            group,
            f"M {right_shoulder} {shoulder_y} L {right_shoulder+45} {shoulder_y+35} L {right_shoulder+18} {armhole_y}",
            outer_stroke
        )

        add_path(
            dwg,
            group,
            f"M {left_shoulder-40} {shoulder_y+38} L {left_shoulder-15} {armhole_y-2}",
            stitch_stroke
        )

        add_path(
            dwg,
            group,
            f"M {right_shoulder+40} {shoulder_y+38} L {right_shoulder+15} {armhole_y-2}",
            stitch_stroke
        )

    # Waist seam
    if waist_seam:
        add_path(
            dwg,
            group,
            f"M {left_waist} {waist_y} C {x-30} {waist_y+5}, {x+30} {waist_y+5}, {right_waist} {waist_y}",
            seam_stroke
        )

    # Center seam
    if center_seam:
        add_path(
            dwg,
            group,
            f"M {x} {top_y+70} L {x} {hem_y}",
            seam_stroke
        )

    # Hem stitch
    if hem_stitch:
        add_path(
            dwg,
            group,
            f"M {left_hem+8} {hem_y-14} C {x-45} {hem_y-5}, {x+45} {hem_y-5}, {right_hem-8} {hem_y-14}",
            stitch_stroke,
            dasharray="3,3"
        )

    # Back zipper
    if view == "Back" and zipper:
        add_path(
            dwg,
            group,
            f"M {x} {top_y+35} L {x} {waist_y+20}",
            seam_stroke
        )

        add_path(
            dwg,
            group,
            f"M {x+5} {top_y+42} L {x+5} {waist_y+15}",
            stitch_stroke,
            dasharray="2,3"
        )

        add_path(
            dwg,
            group,
            f"M {x-5} {top_y+42} L {x-5} {waist_y+15}",
            stitch_stroke,
            dasharray="2,3"
        )

    # Label text
    group.add(
        dwg.text(
            view.upper(),
            insert=(x-25, y-35),
            font_size="18px",
            font_family="Arial",
            fill="black"
        )
    )


def build_svg():
    width = 900
    height = 650

    svg_io = StringIO()

    dwg = svgwrite.Drawing(
        svg_io,
        size=(width, height),
        viewBox=f"0 0 {width} {height}",
        profile="tiny"
    )

    front_group = dwg.g(id="Front_Flat")
    back_group = dwg.g(id="Back_Flat")

    draw_dress(
        dwg,
        front_group,
        260,
        105,
        "Front",
        dress_type,
        neckline,
        sleeve,
        waist_seam,
        center_front_seam,
        hem_stitch,
        False,
        outer_stroke,
        seam_stroke,
        stitch_stroke
    )

    draw_dress(
        dwg,
        back_group,
        640,
        105,
        "Back",
        dress_type,
        neckline,
        sleeve,
        waist_seam,
        center_back_seam,
        hem_stitch,
        back_zipper,
        outer_stroke,
        seam_stroke,
        stitch_stroke
    )

    dwg.add(front_group)
    dwg.add(back_group)

    dwg.write(svg_io)

    return svg_io.getvalue().encode("utf-8")


svg_bytes = build_svg()

st.subheader("Preview")
st.image(svg_bytes, use_column_width=True)

st.download_button(
    "Download Editable SVG",
    data=svg_bytes,
    file_name="real_flats_ai_dress_generator_v1.svg",
    mime="image/svg+xml"
)

st.info(
    "Open the SVG in Illustrator. The dress is built from editable stroke paths with separate Front_Flat and Back_Flat groups."
)    )

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
