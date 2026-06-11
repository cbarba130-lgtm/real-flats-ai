import streamlit as st
import cv2
import numpy as np
import svgwrite
from skimage.morphology import skeletonize
from scipy.ndimage import distance_transform_edt
from io import BytesIO
from PIL import Image

APP_NAME = "Real Flats AI"
TAGLINE = "Turn sketches into editable fashion flats."

st.set_page_config(page_title=APP_NAME, layout="wide")

st.title(APP_NAME)
st.caption(TAGLINE)

st.markdown("""
Upload a clean black-and-white CAD flat sketch.  
The app exports an Illustrator-compatible SVG using editable **stroke paths**, not filled Image Trace objects.
""")

uploaded_file = st.file_uploader(
    "Upload a flat sketch",
    type=["jpg", "jpeg", "png", "tif", "tiff"]
)

with st.sidebar:
    st.header("Vector Settings")

    threshold_mode = st.radio(
        "Threshold mode",
        ["Auto", "Manual"],
        index=0,
        help="Auto usually works best for clean CAD flats."
    )

    manual_threshold = st.slider(
        "Manual black/white threshold",
        0,
        255,
        165,
        disabled=(threshold_mode == "Auto")
    )

    speck_area = st.slider(
        "Remove specks smaller than",
        0,
        500,
        20,
        help="Higher removes more tiny marks. Use low values if stitch dots disappear."
    )

    smoothness = st.slider(
        "Path smoothing",
        0.0,
        5.0,
        1.0,
        0.1,
        help="Higher creates simpler paths but may reduce detail."
    )

    preserve_line_weights = st.checkbox(
        "Preserve line-weight hierarchy",
        value=True
    )

    min_stroke = st.slider("Minimum stroke weight", 0.25, 3.0, 0.5, 0.05)
    max_stroke = st.slider("Maximum stroke weight", 0.5, 8.0, 3.0, 0.05)

    remove_texture_details = st.checkbox(
        "Remove texture details",
        value=False,
        help="Experimental. For v0.1, use speck removal to reduce small texture marks."
    )

    st.divider()

    st.write("Output")
    separate_front_back = st.checkbox("Separate front/back into SVG groups", value=True)
    include_preview_layer = st.checkbox("Include white background in SVG", value=False)


def load_grayscale(uploaded_bytes):
    arr = np.frombuffer(uploaded_bytes, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
    if img is None:
        pil_img = Image.open(BytesIO(uploaded_bytes)).convert("L")
        img = np.array(pil_img)
    return img


def preprocess(img, threshold_mode, manual_threshold, speck_area):
    # Light blur helps eliminate JPEG fuzz without destroying CAD linework
    blur = cv2.GaussianBlur(img, (3, 3), 0)

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

    # Remove tiny connected components
    if speck_area > 0:
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(bw, 8)
        cleaned = np.zeros_like(bw)
        for i in range(1, num_labels):
            area = stats[i, cv2.CC_STAT_AREA]
            if area >= speck_area:
                cleaned[labels == i] = 255
        bw = cleaned

    return bw


def estimate_stroke_weight(point, distance_map, min_stroke, max_stroke, preserve=True):
    if not preserve:
        return (min_stroke + max_stroke) / 2

    x, y = int(point[0]), int(point[1])
    h, w = distance_map.shape
    if x < 0 or x >= w or y < 0 or y >= h:
        return min_stroke

    # Distance to nearest background approximates half the original line thickness.
    thickness_px = max(1.0, distance_map[y, x] * 2.0)

    # Map pixel thickness into Illustrator-friendly stroke range.
    # This preserves hierarchy more than exact physical point size.
    stroke = thickness_px * 0.45
    return float(np.clip(stroke, min_stroke, max_stroke))


def contour_to_path(points):
    if len(points) < 2:
        return None

    d = f"M {points[0][0]:.2f} {points[0][1]:.2f}"
    for p in points[1:]:
        d += f" L {p[0]:.2f} {p[1]:.2f}"
    return d


def split_front_back_groups(contours, width):
    # Simple v0.1 grouping: paths left of center = Front, paths right of center = Back.
    # This is intentionally transparent and easy to improve later.
    front, back, center = [], [], []
    midpoint = width / 2

    for contour in contours:
        pts = contour.squeeze()
        if len(pts.shape) != 2:
            continue
        x_mean = np.mean(pts[:, 0])
        if x_mean < midpoint * 0.92:
            front.append(contour)
        elif x_mean > midpoint * 1.08:
            back.append(contour)
        else:
            center.append(contour)

    return front, back, center


def build_svg(img, bw, smoothness, preserve_line_weights, min_stroke, max_stroke,
              separate_front_back=True, include_preview_layer=False):
    h, w = bw.shape

    # Distance map from original binary line art, used to estimate local line thickness.
    distance_map = distance_transform_edt(bw > 0)

    # Centerline skeleton
    skeleton = skeletonize(bw > 0)
    skeleton_u8 = (skeleton * 255).astype(np.uint8)

    contours, _ = cv2.findContours(
        skeleton_u8,
        cv2.RETR_LIST,
        cv2.CHAIN_APPROX_NONE
    )

    svg_io = BytesIO()
    dwg = svgwrite.Drawing(
        svg_io,
        size=(w, h),
        viewBox=f"0 0 {w} {h}",
        profile="tiny"
    )

    dwg.add(dwg.desc(
        "Generated by Real Flats AI v0.1. Editable stroke paths. Fill set to none."
    ))

    if include_preview_layer:
        bg = dwg.g(id="White_Background")
        bg.add(dwg.rect(insert=(0, 0), size=(w, h), fill="white"))
        dwg.add(bg)

    def add_contours_to_group(group, contour_list):
        for contour in contour_list:
            if len(contour) < 4:
                continue

            epsilon = (smoothness / 100.0) * cv2.arcLength(contour, False)
            approx = cv2.approxPolyDP(contour, epsilon, False) if smoothness > 0 else contour
            points = approx.squeeze()

            if len(points.shape) != 2 or len(points) < 2:
                continue

            d = contour_to_path(points)
            if not d:
                continue

            mid_point = points[len(points) // 2]
            stroke_width = estimate_stroke_weight(
                mid_point,
                distance_map,
                min_stroke,
                max_stroke,
                preserve_line_weights
            )

            group.add(dwg.path(
                d=d,
                fill="none",
                stroke="black",
                stroke_width=stroke_width,
                stroke_linecap="round",
                stroke_linejoin="round"
            ))

    if separate_front_back:
        front, back, center = split_front_back_groups(contours, w)

        g_front = dwg.g(id="Front_Flat")
        g_back = dwg.g(id="Back_Flat")
        g_details = dwg.g(id="Center_or_Unsorted_Details")

        add_contours_to_group(g_front, front)
        add_contours_to_group(g_back, back)
        add_contours_to_group(g_details, center)

        dwg.add(g_front)
        dwg.add(g_back)
        if center:
            dwg.add(g_details)
    else:
        g_all = dwg.g(id="Editable_Stroke_Paths")
        add_contours_to_group(g_all, contours)
        dwg.add(g_all)

    dwg.write(svg_io)
    svg_io.seek(0)

    return svg_io.getvalue(), skeleton_u8


if uploaded_file:
    file_bytes = uploaded_file.read()
    img = load_grayscale(file_bytes)

    bw = preprocess(
        img,
        threshold_mode,
        manual_threshold,
        speck_area
    )

    svg_bytes, skeleton_preview = build_svg(
        img,
        bw,
        smoothness,
        preserve_line_weights,
        min_stroke,
        max_stroke,
        separate_front_back,
        include_preview_layer
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("Original")
        st.image(img, clamp=True, use_container_width=True)

    with col2:
        st.subheader("Cleaned Line Art")
        st.image(bw, clamp=True, use_container_width=True)

    with col3:
        st.subheader("Centerline Preview")
        st.image(skeleton_preview, clamp=True, use_container_width=True)

    st.download_button(
        "Download Illustrator-Compatible SVG",
        data=svg_bytes,
        file_name="real_flats_ai_export.svg",
        mime="image/svg+xml"
    )

    st.info(
        "Open the SVG in Illustrator. Lines should come in as editable paths with Fill=None and Stroke=black. "
        "Then save as .AI from Illustrator."
    )

else:
    st.info("Upload a clean CAD flat sketch to begin.")