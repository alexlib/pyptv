# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "marimo>=0.19.9",
#     "matplotlib==3.10.8",
#     "numpy==2.4.2",
#     "optv==0.3.0",
#     "pandas==3.0.0",
#     "pydantic-ai==1.56.0",
#     "pyzmq>=27.1.0",
#     "scikit-image==0.26.0",
# ]
# ///

import marimo

__generated_with = "0.19.9"
app = marimo.App(width="full", auto_download=["ipynb"])


@app.cell
def _():
    import marimo as mo
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt

    from dataclasses import dataclass
    from pathlib import Path
    import sys

    from skimage.color import rgb2gray
    from skimage.io import imread
    from skimage.util import img_as_ubyte

    from optv.segmentation import target_recognition

    return (
        Path,
        img_as_ubyte,
        imread,
        mo,
        np,
        pd,
        plt,
        rgb2gray,
        sys,
        target_recognition,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Detection UI (Marimo)

    Interactive replica of `pyptv/detection_gui.py`:

    - Load an image from a working directory
    - Apply **inverse** and/or **highpass** preprocessing
    - Tune detection parameters (threshold, size/pixel bounds, etc.)
    - Run particle detection (`optv.segmentation.target_recognition`)
    - Visualize detected particle centers overlaid on the image
    """)
    return


@app.cell
def _(Path, sys):
    # Allow running directly from repo root without installation
    repo_root = Path(".").resolve()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from pyptv import ptv

    return (ptv,)


@app.cell
def _(mo):
    working_dir = mo.ui.text(
        label="Working directory",
        value="tests/test_cavity",
        full_width=True,
    )
    image_name = mo.ui.text(
        label="Image path (relative to working directory or absolute)",
        value="cal/cam1.tif",
        full_width=True,
    )

    hp_flag = mo.ui.checkbox(label="Highpass", value=False)
    inverse_flag = mo.ui.checkbox(label="Inverse", value=False)

    controls_top = mo.vstack(
        [
            working_dir,
            image_name,
            mo.hstack([hp_flag, inverse_flag], justify="start"),
        ]
    )
    controls_top
    return hp_flag, image_name, inverse_flag, working_dir


@app.cell
def _(mo):
    # Detection parameters (kept wide enough to avoid needing dynamic slider ranges)
    grey_thresh = mo.ui.slider(1, 255, value=40, label="Grey threshold")

    min_npix = mo.ui.slider(0, 2000, value=25, label="Min pixels")
    max_npix = mo.ui.slider(1, 5000, value=400, label="Max pixels")

    min_npix_x = mo.ui.slider(1, 500, value=5, label="Min pixels in x")
    max_npix_x = mo.ui.slider(1, 500, value=50, label="Max pixels in x")

    min_npix_y = mo.ui.slider(1, 500, value=5, label="Min pixels in y")
    max_npix_y = mo.ui.slider(1, 500, value=50, label="Max pixels in y")

    disco = mo.ui.slider(0, 255, value=100, label="Discontinuity")
    sum_of_grey = mo.ui.slider(0, 20000, value=100, label="Sum of greyvalue")

    auto_detect = mo.ui.checkbox(label="Auto-detect on change", value=True)
    detect_btn = mo.ui.run_button(label="Detect")

    controls_det = mo.vstack(
        [
            grey_thresh,
            mo.hstack([min_npix, max_npix], gap=1),
            mo.hstack([min_npix_x, max_npix_x], gap=1),
            mo.hstack([min_npix_y, max_npix_y], gap=1),
            disco,
            sum_of_grey,
            mo.hstack([auto_detect, detect_btn], justify="start"),
        ]
    )

    controls_det
    return (
        auto_detect,
        detect_btn,
        disco,
        grey_thresh,
        max_npix,
        max_npix_x,
        max_npix_y,
        min_npix,
        min_npix_x,
        min_npix_y,
        sum_of_grey,
    )


@app.cell
def _(
    Path,
    hp_flag,
    image_name,
    img_as_ubyte,
    imread,
    inverse_flag,
    mo,
    rgb2gray,
    working_dir,
):
    wd = Path(working_dir.value).expanduser().resolve()

    if image_name.value.strip() == "":
        mo.stop("Provide an image path.")

    img_path = Path(image_name.value).expanduser()
    if not img_path.is_absolute():
        img_path = wd / img_path

    if not wd.exists():
        mo.stop(f"Working directory not found: {wd}")

    if not img_path.exists():
        mo.stop(f"Image not found: {img_path}")

    raw_image = imread(img_path)
    if raw_image.ndim > 2:
        raw_image = rgb2gray(raw_image)
    raw_image = img_as_ubyte(raw_image)

    # Process image (inverse/highpass are applied in next cell)
    info = mo.md(
        f"""
        **Loaded**: `{img_path}`  \
        Shape: `{raw_image.shape}`  \
        Highpass: `{hp_flag.value}` / Inverse: `{inverse_flag.value}`
        """
    )

    info
    return (raw_image,)


@app.cell
def _(hp_flag, inverse_flag, mo, np, ptv, raw_image):
    # Build control params similar to detection_gui.py
    cpar = ptv.ControlParams(1)
    cpar.set_image_size((raw_image.shape[1], raw_image.shape[0]))
    cpar.set_pixel_size((0.01, 0.01))
    cpar.set_hp_flag(hp_flag.value)

    im = raw_image.copy()
    if inverse_flag.value:
        im = 255 - im

    if hp_flag.value:
        # Match original GUI: ptv.preprocess_image(im, 0, cpar, 25)
        try:
            im = ptv.preprocess_image(im, 0, cpar, 25)
        except Exception as exc:
            mo.stop(f"Highpass preprocessing failed: {exc}")

    processed_image = np.asarray(im)
    return cpar, processed_image


@app.cell
def _(
    auto_detect,
    cpar,
    detect_btn,
    disco,
    grey_thresh,
    max_npix,
    max_npix_x,
    max_npix_y,
    min_npix,
    min_npix_x,
    min_npix_y,
    mo,
    pd,
    processed_image,
    ptv,
    sum_of_grey,
    target_recognition,
):
    should_run = auto_detect.value or detect_btn.value
    if not should_run:
        mo.stop("Detection is paused. Enable auto-detect or click Detect.")

    # Build target params
    tpar = ptv.TargetParams()
    tpar.set_grey_thresholds([int(grey_thresh.value), 0, 0, 0])

    # Enforce consistent bounds
    min_pix = int(min_npix.value)
    max_pix = int(max_npix.value)
    if max_pix <= min_pix:
        max_pix = min_pix + 1

    min_x = int(min_npix_x.value)
    max_x = int(max_npix_x.value)
    if max_x <= min_x:
        max_x = min_x + 1

    min_y = int(min_npix_y.value)
    max_y = int(max_npix_y.value)
    if max_y <= min_y:
        max_y = min_y + 1

    tpar.set_pixel_count_bounds([min_pix, max_pix])
    tpar.set_xsize_bounds([min_x, max_x])
    tpar.set_ysize_bounds([min_y, max_y])
    tpar.set_min_sum_grey(int(sum_of_grey.value))
    tpar.set_max_discontinuity(int(disco.value))

    # Run detection
    try:
        targs = target_recognition(processed_image, tpar, 0, cpar)
        targs.sort_y()
    except Exception as exc:
        mo.stop(f"Detection failed: {exc}")

    xs = [float(t.pos()[0]) for t in targs]
    ys = [float(t.pos()[1]) for t in targs]

    df = pd.DataFrame({"x": xs, "y": ys})

    summary = mo.md(f"**Detected**: {len(df)} particles")
    summary
    return (df,)


@app.cell
def _(df, mo, plt, processed_image):
    fig, ax = plt.subplots(figsize=(9, 9))
    ax.imshow(processed_image, cmap="gray")
    if len(df) > 0:
        ax.scatter(df["x"], df["y"], s=20, c="orange", linewidths=0)
    ax.set_title("Detection overlay")
    ax.axis("off")
    plt.close(fig)

    mo.vstack(
        [
            fig,
            mo.ui.table(df.head(200), label="First 200 detections"),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
