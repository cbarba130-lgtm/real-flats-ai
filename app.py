import streamlit as st
import cv2
import numpy as np
import svgwrite
from skimage.morphology import skeletonize
from scipy.ndimage import distance_transform_edt
from io import BytesIO, StringIO
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
        index=0
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
        20
    )

    smoothness = st.slider(
        "Path smoothing",
        0.0,
        5.0,
        1.0,
        0.1
    )

    preserve_line_weights = st.checkbox(
        "Preserve line-weight hierarchy",
        value=True
    )

    min_stroke = st.slider("Minimum stroke weight", 0.25, 3.0, 0.5, 0.05)
    max_stroke = st.slider("Maximum stroke weight", 0.5, 8.0, 3.0, 0.05)

    remove_texture_details = st.checkbox(
        "Remove texture details",
        value=False
    )

    st.divider()

    separate_front_back = st.checkbox(
        "Separate front/back into SVG groups",
        value=True
    )

    include_preview_layer = st.checkbox(
        "Include white background in SVG",
        value=False
    )


def load_grayscale(uploaded_bytes):
    arr = np.frombuffer(uploaded_bytes, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)

    if img is None:
        pil_img = Image.open(BytesIO(uploaded_bytes)).convert("L")
        img = np.array(pil_img)

    return img


def preprocess(img, threshold_mode, manual_threshold, speck_area):
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
    height, width = distance_map.shape

    if x < 0 or x >= width or y < 0 or y >= height:
        return min_stroke

    thickness_px = max(1.0, distance_map[y, x] * 2.0)

    stroke = thickness_px * 0.45
    stroke = float(np.clip(stroke, min_stroke, max_stroke))

    return stroke


def contour_to_path(points):
    if len(points) < 2:
        return None

    d = f"M {points[0][0]:.2f} {points[0][1]:.2f}"

    for point in points[1:]:
        d += f" L {point[0]:.2f} {point[1]:.2f}"

    return d


def split_front_back_groups(contours, width):
    front = []
    back = []
    center = []

    midpoint = width / 2

    for contour in contours:
        points = contour.squeeze()

        if len(points.shape) != 2:
            continue

        x_mean = np.mean(points[:, 0])

        if x_mean < midpoint * 0.92:
            front.append(contour)
        elif x_mean > midpoint * 1.08:
            back.append(contour)
        else:
            center.append(contour)

    return front, back, center


def build_svg(
    bw,
    smoothness,
    preserve_line_weights,
    min_stroke,
    max_stroke,
    separate_front_back=True,
    include_preview_layer=False
):
    height, width = bw.shape

    distance_map = distance_transform_edt(bw > 0)

    skeleton = skeletonize(bw > 0)
    skeleton_u8 = (skeleton * 255).astype(np.uint8)

    contours, _ = cv2.findContours(
        skeleton_u8,
        cv2.RETR_LIST,
        cv2.CHAIN_APPROX_NONE
    )

    svg_io = StringIO()

dwg = svgwrite.Drawing(
    svg_io,
    size=(width, height),
    viewBox=f"0 0 {width} {height}",
    profile="tiny"
    )

    if include_preview_layer:
        bg = dwg.g(id="White_Background")
        bg.add(dwg.rect(insert=(0, 0), size=(width, height), fill="white"))
        dwg.add(bg)

    def add_contours_to_group(group, contour_list):
        for contour in contour_list:
            if len(contour) < 4:
                continue

            if smoothness > 0:
                epsilon = (smoothness / 100.0) * cv2.arcLength(contour, False)
                approx = cv2.approxPolyDP(contour, epsilon, False)
            else:
                approx = contour

            points = approx.squeeze()

            if len(points.shape) != 2 or len(points) < 2:
                continue

            path_data = contour_to_path(points)

            if not path_data:
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
                d=path_data,
                fill="none",
                stroke="black",
                stroke_width=stroke_width,
                stroke_linecap="round",
                stroke_linejoin="round"
            ))

    if separate_front_back:
        front, back, center = split_front_back_groups(contours, width)

        front_group = dwg.g(id="Front_Flat")
        back_group = dwg.g(id="Back_Flat")
        center_group = dwg.g(id="Center_or_Unsorted_Details")

        add_contours_to_group(front_group, front)
        add_contours_to_group(back_group, back)
        add_contours_to_group(center_group, center)

        dwg.add(front_group)
        dwg.add(back_group)

        if center:
            dwg.add(center_group)

    else:
        all_group = dwg.g(id="Editable_Stroke_Paths")
        add_contours_to_group(all_group, contours)
        dwg.add(all_group)

    dwg.write(svg_io)

svg_text = svg_io.getvalue()
svg_bytes = svg_text.encode("utf-8")

return svg_bytes, skeleton_u8


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
        "Open the SVG in Illustrator. Lines should come in as editable paths with Fill=None and Stroke=black. Then save as .AI from Illustrator."
    )

else:
    st.info("Upload a clean CAD flat sketch to begin.")
