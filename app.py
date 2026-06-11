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
)
