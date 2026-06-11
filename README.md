# Real Flats AI v0.1

**Turn sketches into editable fashion flats.**

This is the first working prototype of Real Flats AI.

It converts clean black-and-white CAD flat sketches into Illustrator-compatible SVG files using editable stroke paths.

## What it does

- Upload JPG, PNG, or TIFF
- Clean black line art
- Remove small specks/noise
- Centerline trace artwork
- Export SVG paths with `fill="none"` and editable stroke lines
- Preserve relative line weights as best as possible
- Put front/back into separate SVG groups

## Important

This does **not** create a native `.ai` file yet.

The intended workflow is:

1. Download SVG
2. Open SVG in Adobe Illustrator
3. Confirm paths are editable strokes
4. Save As `.ai`

## How to run on Mac

### Step 1: Install Python

Go to:

https://www.python.org/downloads/

Download and install Python 3.

### Step 2: Open Terminal

Open the Real Flats AI folder.

Right-click the folder and choose **New Terminal at Folder** if available.

Or open Terminal and type:

```bash
cd path/to/real_flats_ai_v0_1
```

### Step 3: Install the app requirements

```bash
pip3 install -r requirements.txt
```

### Step 4: Run the app

```bash
streamlit run app.py
```

A browser page will open.

## How to use the app

1. Upload a clean CAD flat sketch
2. Adjust settings if needed
3. Review the cleaned preview and centerline preview
4. Download the SVG
5. Open the SVG in Illustrator

## Illustrator check

When you click a line in Illustrator, the ideal result is:

- Object type: Path
- Fill: None
- Stroke: Black
- Stroke weight: editable

That means it worked.

## Known limitations in v0.1

- Front/back separation is simple and based on left/right position
- Stitches and texture details are preserved, but may create many paths
- Some curved paths may be segmented
- Native AI export is not included yet
- Best results require clean CAD flats on a white background

## Recommended input

Good:

- Clean technical CAD flats
- Black linework
- White or light background
- Front and back views
- No heavy shadows or color fills

Not supported yet:

- Hand pencil sketches
- Photos of garments
- Color fashion illustrations
- Low-resolution screenshots