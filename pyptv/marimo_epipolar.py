import marimo

__generated_with = "0.20.2"
app = marimo.App(width="full")

with app.setup:
    import marimo as mo
    from optv.epipolar import epipolar_curve
    from optv.imgcoord import image_coordinates
    from optv.transforms import convert_arr_metric_to_pixel
    from optv.image_processing import preprocess_image
    from optv.calibration import Calibration

    from pyptv.parameter_manager import ParameterManager
    from pyptv.experiment import Experiment
    from pathlib import Path
    import matplotlib.pyplot as plt
    import imageio.v3 as iio
    import numpy as np
    import matplotlib
    from optv.parameters import ControlParams, VolumeParams
    from pyptv import ptv

    from optv.segmentation import target_recognition
    from optv.correspondences import MatchedCoords, correspondences


@app.cell
def _():
    # load parameters from the YAML file
    _yaml_path = '/home/user/Downloads/Illmenau/pyPTV_folder/parameters_Run4.yaml'

    yaml_path = Path(_yaml_path).expanduser().resolve()
    assert yaml_path.exists()

    pm = ParameterManager()
    pm.from_yaml(yaml_path)
    exp = Experiment(pm=pm)

    params = pm.parameters
    num_cams = int(params.get("num_cams", pm.num_cams or 0) or 0)
    print(f"Number of cameras: {num_cams} in {yaml_path}")
    return num_cams, pm, yaml_path


@app.cell
def _(num_cams, pm, yaml_path):


    cals = []
    images = []

    ptv_params = pm.parameters.get('ptv', {})
    img_names = ptv_params.get('img_name', [])
    cal_img_names = ptv_params.get('img_cal', [])

    # Let's try to get them directly.
    cal_ori = pm.parameters.get('cal_ori', {})
    ori_names = cal_ori.get('img_ori', [])

    base_path = Path(yaml_path).parent

    for i in range(num_cams):
        # Images
        img_path = img_names[i]
        if not Path(img_path).is_absolute():
            img_path = base_path / img_path

        try:
            img = iio.imread(img_path)
            images.append(img)
        except Exception as e:
            print(f"Failed to load image {img_path}: {e}")
            # fallback to a blank image
            images.append(np.zeros((ptv_params.get('imy', 1024), ptv_params.get('imx', 1024))))

        # Calibrations
        cal = Calibration()

        # Try using the logic from ptv.py: base name from cal_ori.img_cal_name
        cal_img_name = cal_ori.get('img_cal_name', cal_img_names)[i]

        # wait, the output of cal_ori shows img_ori: ['cal/run3/cam1.tif.ori', ...]
        ori_file_path = base_path / ori_names[i]

        # In PTV, addpar file has .addpar extension but what is the exact name? 
        # Usually it's base name + .addpar, i.e., without .tif.ori?
        # Let's just check if it's ori_names[i] replacing .tif.ori with .addpar
        # or .ori with .addpar
        addpar_file_path = Path(str(ori_file_path).replace('.ori', '') + '.addpar')
        if not addpar_file_path.exists():
            addpar_file_path = Path(str(ori_file_path).replace('.tif.ori', '') + '.addpar')

        if ori_file_path.exists() and addpar_file_path.exists():
            cal.from_file(str(ori_file_path), str(addpar_file_path))
            print(f"Loaded calibration from {ori_file_path} and {addpar_file_path}")
        else:
            print(f"Missing calibration files for camera {i+1}: {ori_file_path} / {addpar_file_path}")

        cals.append(cal)
    return cals, images


@app.cell
def _(num_cams, pm):
    cpar = ptv._populate_cpar(pm.parameters['ptv'], num_cams)
    vpar = ptv._populate_vpar(pm.parameters['criteria']) if 'criteria' in pm.parameters else VolumeParams()

    print("cpar image size:", cpar.get_image_size())
    return cpar, vpar


@app.cell
def _(cpar, images, pm):
    images_8bit = [ptv.img_as_ubyte(im) for im in images]

    # # Check if negative flag is set, if so, invert the 8-bit images
    is_negative = pm.parameters.get('ptv', {}).get('negative', False)
    if is_negative:
        # Invert images: 255 - image
        images_8bit = [np.clip(255 - im, 0, 255) for im in images_8bit]
        print("Applied negative inversion to images.")

    images_8bit = [ptv.simple_highpass(img, cpar) for img in images_8bit]
    return (images_8bit,)


@app.cell
def _(images_8bit):
    # Visualize the first image after applying the highpass filter
    _fig, _ax = plt.subplots(figsize=(8, 6))
    _ax.imshow(images_8bit[0], cmap='gray')
    _ax.set_title("Highpass Filtered Image (Camera 1)")
    _ax.axis('off')
    _ax
    return


@app.cell
def _(num_cams, pm):
    tpar = ptv._populate_tpar(pm.parameters, num_cams)
    tpar.get_grey_thresholds()
    return (tpar,)


@app.cell
def _(cals, cpar, images_8bit, tpar, vpar):
    targets = []
    matched = []

    for i_cam, im in enumerate(images_8bit):
        targs = target_recognition(im, tpar, i_cam, cpar)
        targs.sort_y()
        targets.append(targs)

        mc = MatchedCoords(targs, cpar, cals[i_cam])
        matched.append(mc)

    sorted_pos, sorted_corresp, num_targs = correspondences(targets, matched, cals, vpar, cpar)

    print(f"Total targets used: {num_targs}")
    print("cpar image size:", cpar.get_image_size())
    print(sorted_pos[0][0, 0, :])
    return (sorted_pos,)


@app.cell
def _(cals, cpar, images, num_cams, sorted_pos, vpar):

    # We create a 2x2 grid of subplots for the 4 cameras
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    axes_flat = axes.flatten()

    # Colors by order of images: red, green, blue, yellow
    colors = ['red', 'green', 'blue', 'yellow']

    for cam_idx in range(num_cams):
        axes_flat[cam_idx].imshow(images[cam_idx], cmap='gray')
        axes_flat[cam_idx].set_title(f"Camera {cam_idx+1}")
        axes_flat[cam_idx].axis('on')
        # Set limits to image bounds and prevent expanding
        img_h, img_w = images[cam_idx].shape[:2]
        axes_flat[cam_idx].set_xlim(0, img_w)
        axes_flat[cam_idx].set_ylim(img_h, 0)
        axes_flat[cam_idx].autoscale(False)

    # Display detected points from correspondences:
    clique_colors = ['red', 'green', 'yellow']
    clique_labels = ['Quadruplets', 'Triplets', 'Pairs']

    for clique_idx, pos_type in enumerate(sorted_pos):
        c_color = clique_colors[clique_idx]
        c_label = clique_labels[clique_idx]

        for cam_idx in range(num_cams):
            if len(pos_type) == 0:
                continue

            pts = pos_type[cam_idx]
            # Filter out invalid points (-999)
            valid = (pts[:, 0] > -900) & (pts[:, 1] > -900)
            valid_pts = pts[valid]
            if len(valid_pts) > 0:
                axes_flat[cam_idx].scatter(
                    valid_pts[:, 0], valid_pts[:, 1],
                    facecolors='none', edgecolors=c_color, s=60,
                    label=c_label if cam_idx == 0 else ""
                )

    # Add a legend to the first subplot to explain the colors
    axes_flat[0].legend(loc='upper right', fontsize=8)

    def onclick(event):
        if not event.inaxes:
            return

        ax = event.inaxes

        # Find which camera was clicked
        clicked_i = None
        for j_cam, a in enumerate(axes_flat):
            if a == ax:
                clicked_i = j_cam
                break

        if clicked_i is None:
            return

        x, y = event.xdata, event.ydata

        # Draw a point on the clicked image
        ax.plot(x, y, 'o', color=colors[clicked_i], markersize=6)

        point = np.array([x, y])
        num_points = 100

        # Draw epipolar lines on other images
        for j_other in range(num_cams):
            if clicked_i == j_other:
                continue

            try:
                pts_epipolar = epipolar_curve(
                    point,
                    cals[clicked_i],
                    cals[j_other],
                    num_points,
                    cpar,
                    vpar
                )

                if len(pts_epipolar) > 1:
                    # Also we can mathematically filter to only those points inside the image
                    img_h, img_w = images[j_other].shape[:2]
                    valid_mask = (pts_epipolar[:, 0] >= 0) & (pts_epipolar[:, 0] <= img_w) & \
                                 (pts_epipolar[:, 1] >= 0) & (pts_epipolar[:, 1] <= img_h)

                    # If you just want it not to exceed the axis visually, 
                    # autoscale(False) and axis limits already handle it!
                    axes_flat[j_other].plot(pts_epipolar[:, 0], pts_epipolar[:, 1], color=colors[clicked_i], linewidth=1.5)
            except Exception as e:
                print(f"Error drawing epipolar line for camera {j_other+1}: {e}")

        fig.canvas.draw_idle()

    # Connect the click event
    cid = fig.canvas.mpl_connect('button_press_event', onclick)

    plt.tight_layout()
    # In Marimo, the last expression is displayed. If the user has an interactive backend,
    # it will support clicks. mo.mpl.interactive(fig) also helps for browser interactivity.
    mo.mpl.interactive(fig)
    return


if __name__ == "__main__":
    app.run()
