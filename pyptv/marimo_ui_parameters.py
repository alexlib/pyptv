import marimo

__generated_with = "0.19.9"
app = marimo.App(width="full", auto_download=["ipynb"])


@app.cell
def _():
    import marimo as mo
    from pathlib import Path
    import sys

    return Path, mo, sys


@app.cell(hide_code=True)
def _(mo):
    import textwrap

    mo.md(
        textwrap.dedent(
            """
            ## Parameters UI (Marimo)

            Marimo replica of `pyptv/parameter_gui.py`:

            - Load a `parameters_*.yaml`
            - Edit **Main**, **Calibration**, and **Tracking** parameters
            - Save back to YAML using the same update rules as the TraitsUI handlers

            Notes:
            - Calibration save updates `man_ori.nr` only (never touches `man_ori_coordinates`).
            """
        ).strip()
    )
    return


@app.cell
def _(Path, sys):
    repo_root = Path(".").resolve()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from pyptv.parameter_manager import ParameterManager
    from pyptv.experiment import Experiment

    return Experiment, ParameterManager


@app.cell
def _(mo):
    yaml_path = mo.ui.text(
        label="YAML path",
        value="tests/test_cavity/parameters_Run1.yaml",
        full_width=True,
    )
    load_btn = mo.ui.run_button(label="Load YAML")

    mo.hstack([yaml_path, load_btn], gap=1)
    return load_btn, yaml_path


@app.cell
def _(Experiment, ParameterManager, Path, load_btn, mo, yaml_path):
    if not load_btn.value:
        mo.stop("Click ‘Load YAML’ to begin.")

    path = Path(yaml_path.value).expanduser().resolve()
    if not path.exists():
        mo.stop(f"YAML not found: {path}")

    pm = ParameterManager()
    pm.from_yaml(path)
    exp = Experiment(pm=pm)

    params = pm.parameters
    num_cams = int(params.get("num_cams", pm.num_cams or 0) or 0)

    mo.md(f"**Loaded**: `{path}`  \\  **num_cams**: `{num_cams}`")
    return exp, num_cams, params, pm


@app.cell
def _(num_cams):
    def list_get(lst, idx, default="---"):
        if not isinstance(lst, list):
            return default
        return lst[idx] if idx < len(lst) and lst[idx] is not None else default


    def sec(params, name):
        v = params.get(name)
        return v if isinstance(v, dict) else {}


    def pair2(v, default0=0, default1=0):
        if isinstance(v, (list, tuple)) and len(v) >= 2:
            return v[0], v[1]
        return default0, default1


    def safe_bool(v, default=False):
        return bool(v) if v is not None else default


    def safe_int(v, default=0):
        try:
            return int(v)
        except Exception:
            return default


    def safe_float(v, default=0.0):
        try:
            return float(v)
        except Exception:
            return default


    def _clamp4(values):
        out = list(values) if isinstance(values, list) else []
        out += ["---"] * (4 - len(out))
        return out[:4]


    def _active_cam_count(v):
        try:
            n = int(v)
        except Exception:
            n = int(num_cams)
        return max(0, min(n, 4))

    return list_get, pair2, safe_bool, safe_float, safe_int, sec


@app.cell
def _(
    list_get,
    mo,
    num_cams,
    pair2,
    params,
    safe_bool,
    safe_float,
    safe_int,
    sec,
):
    _ptv = sec(params, "ptv")
    _targ_rec = sec(params, "targ_rec")
    _seq = sec(params, "sequence")
    _criteria = sec(params, "criteria")
    _masking = sec(params, "masking")
    _pft_version = sec(params, "pft_version")

    ui_num_cams = mo.ui.number(
        label="Number of cameras",
        value=safe_int(params.get("num_cams", num_cams), 2) or 2,
        step=1,
    )

    ui_splitter = mo.ui.checkbox(
        label="Splitter", value=safe_bool(_ptv.get("splitter"), False)
    )
    ui_allcam = mo.ui.checkbox(
        label="Accept only points seen from all cameras?",
        value=safe_bool(_ptv.get("allcam_flag"), False),
    )
    ui_hp = mo.ui.checkbox(
        label="High pass filter", value=safe_bool(_ptv.get("hp_flag"), False)
    )

    ui_tiff = mo.ui.checkbox(
        label="TIFF", value=safe_bool(_ptv.get("tiff_flag"), True)
    )
    ui_imx = mo.ui.number(
        label="Image width (imx)", value=safe_int(_ptv.get("imx"), 0), step=1
    )
    ui_imy = mo.ui.number(
        label="Image height (imy)", value=safe_int(_ptv.get("imy"), 0), step=1
    )
    ui_pix_x = mo.ui.number(
        label="Pixel size X (pix_x)",
        value=safe_float(_ptv.get("pix_x"), 0.0),
        step=0.00001,
    )
    ui_pix_y = mo.ui.number(
        label="Pixel size Y (pix_y)",
        value=safe_float(_ptv.get("pix_y"), 0.0),
        step=0.00001,
    )
    ui_chfield = mo.ui.number(
        label="chfield", value=safe_int(_ptv.get("chfield"), 0), step=1
    )

    ui_mmp_n1 = mo.ui.number(
        label="Refractive index air (mmp_n1)",
        value=safe_float(_ptv.get("mmp_n1"), 1.0),
        step=0.0001,
    )
    ui_mmp_n2 = mo.ui.number(
        label="Refractive index glass (mmp_n2)",
        value=safe_float(_ptv.get("mmp_n2"), 1.0),
        step=0.0001,
    )
    ui_mmp_n3 = mo.ui.number(
        label="Refractive index water (mmp_n3)",
        value=safe_float(_ptv.get("mmp_n3"), 1.0),
        step=0.0001,
    )
    ui_mmp_d = mo.ui.number(
        label="Glass thickness (mmp_d)",
        value=safe_float(_ptv.get("mmp_d"), 0.0),
        step=0.001,
    )

    img_name = _ptv.get("img_name", [])
    img_cal = _ptv.get("img_cal", [])

    ui_img_name = [
        mo.ui.text(
            label=f"Name of {i + 1}. image",
            value=str(list_get(img_name, i, "---")),
            full_width=True,
        )
        for i in range(4)
    ]
    ui_img_cal = [
        mo.ui.text(
            label=f"Calibration data for {i + 1}. image",
            value=str(list_get(img_cal, i, "---")),
            full_width=True,
        )
        for i in range(4)
    ]

    gvthres = _targ_rec.get("gvthres", [])
    ui_gvth = [
        mo.ui.number(
            label=f"Gray threshold cam {i + 1}",
            value=safe_int(list_get(gvthres, i, 0), 0),
            step=1,
        )
        for i in range(4)
    ]

    ui_nnmin = mo.ui.number(
        label="min npix (nnmin)", value=safe_int(_targ_rec.get("nnmin"), 0), step=1
    )
    ui_nnmax = mo.ui.number(
        label="max npix (nnmax)", value=safe_int(_targ_rec.get("nnmax"), 0), step=1
    )
    ui_nxmin = mo.ui.number(
        label="min npix x (nxmin)",
        value=safe_int(_targ_rec.get("nxmin"), 0),
        step=1,
    )
    ui_nxmax = mo.ui.number(
        label="max npix x (nxmax)",
        value=safe_int(_targ_rec.get("nxmax"), 0),
        step=1,
    )
    ui_nymin = mo.ui.number(
        label="min npix y (nymin)",
        value=safe_int(_targ_rec.get("nymin"), 0),
        step=1,
    )
    ui_nymax = mo.ui.number(
        label="max npix y (nymax)",
        value=safe_int(_targ_rec.get("nymax"), 0),
        step=1,
    )
    ui_sumg = mo.ui.number(
        label="Sum grey (sumg_min)",
        value=safe_int(_targ_rec.get("sumg_min"), 0),
        step=1,
    )
    ui_disco = mo.ui.number(
        label="Discontinuity (disco)",
        value=safe_int(_targ_rec.get("disco"), 0),
        step=1,
    )
    ui_cr_sz = mo.ui.number(
        label="Cross size (cr_sz)",
        value=safe_int(_targ_rec.get("cr_sz"), 0),
        step=1,
    )

    ui_existing_target = mo.ui.checkbox(
        label="Use existing_target files?",
        value=safe_bool(_pft_version.get("Existing_Target"), False),
    )

    base_name = _seq.get("base_name", [])
    ui_base_name = [
        mo.ui.text(
            label=f"Basename for cam {i + 1}",
            value=str(list_get(base_name, i, "---")),
            full_width=True,
        )
        for i in range(4)
    ]
    ui_seq_first = mo.ui.number(
        label="Sequence first", value=safe_int(_seq.get("first"), 0), step=1
    )
    ui_seq_last = mo.ui.number(
        label="Sequence last", value=safe_int(_seq.get("last"), 0), step=1
    )

    Xmin, Xmax = pair2(_criteria.get("X_lay"), 0, 0)
    Zmin1, Zmin2 = pair2(_criteria.get("Zmin_lay"), 0, 0)
    Zmax1, Zmax2 = pair2(_criteria.get("Zmax_lay"), 0, 0)

    ui_Xmin = mo.ui.number(label="Xmin", value=safe_int(Xmin, 0), step=1)
    ui_Xmax = mo.ui.number(label="Xmax", value=safe_int(Xmax, 0), step=1)
    ui_Zmin1 = mo.ui.number(label="Zmin 1", value=safe_int(Zmin1, 0), step=1)
    ui_Zmin2 = mo.ui.number(label="Zmin 2", value=safe_int(Zmin2, 0), step=1)
    ui_Zmax1 = mo.ui.number(label="Zmax 1", value=safe_int(Zmax1, 0), step=1)
    ui_Zmax2 = mo.ui.number(label="Zmax 2", value=safe_int(Zmax2, 0), step=1)

    ui_cnx = mo.ui.number(
        label="cnx", value=safe_float(_criteria.get("cnx"), 0.0), step=0.01
    )
    ui_cny = mo.ui.number(
        label="cny", value=safe_float(_criteria.get("cny"), 0.0), step=0.01
    )
    ui_cn = mo.ui.number(
        label="cn", value=safe_float(_criteria.get("cn"), 0.0), step=0.01
    )
    ui_csumg = mo.ui.number(
        label="csumg", value=safe_float(_criteria.get("csumg"), 0.0), step=0.01
    )
    ui_corrmin = mo.ui.number(
        label="corrmin", value=safe_float(_criteria.get("corrmin"), 0.0), step=0.1
    )
    ui_eps0 = mo.ui.number(
        label="eps0", value=safe_float(_criteria.get("eps0"), 0.0), step=0.01
    )

    ui_mask_flag = mo.ui.checkbox(
        label="Subtract mask", value=safe_bool(_masking.get("mask_flag"), False)
    )
    ui_mask_base = mo.ui.text(
        label="Mask base name",
        value=str(_masking.get("mask_base_name", "")),
        full_width=True,
    )

    save_main_btn = mo.ui.run_button(label="Save Main Parameters")

    main_tab = mo.vstack(
        [
            mo.md("### General"),
            mo.hstack([ui_num_cams, ui_splitter, ui_allcam], gap=1),
            mo.hstack([ui_hp, ui_tiff], gap=1),
            mo.hstack([ui_imx, ui_imy, ui_chfield], gap=1),
            mo.hstack([ui_pix_x, ui_pix_y], gap=1),
            mo.md("### Refractive indices"),
            mo.hstack([ui_mmp_n1, ui_mmp_n2, ui_mmp_n3, ui_mmp_d], gap=1),
            mo.md("### Images"),
            mo.hstack([mo.vstack(ui_img_name), mo.vstack(ui_img_cal)], gap=2),
            mo.md("### Particle recognition (targ_rec)"),
            mo.hstack([mo.vstack(ui_gvth[:2]), mo.vstack(ui_gvth[2:])], gap=2),
            mo.hstack([ui_nnmin, ui_nnmax, ui_sumg, ui_disco, ui_cr_sz], gap=1),
            mo.hstack([ui_nxmin, ui_nxmax, ui_nymin, ui_nymax], gap=1),
            ui_existing_target,
            mo.md("### Sequence"),
            mo.hstack([ui_seq_first, ui_seq_last], gap=1),
            mo.vstack(ui_base_name),
            mo.md("### Criteria"),
            mo.hstack(
                [ui_Xmin, ui_Xmax, ui_Zmin1, ui_Zmin2, ui_Zmax1, ui_Zmax2], gap=1
            ),
            mo.hstack(
                [ui_cnx, ui_cny, ui_cn, ui_csumg, ui_corrmin, ui_eps0], gap=1
            ),
            mo.hstack([ui_mask_flag, ui_mask_base], gap=1),
            save_main_btn,
        ]
    )
    return (
        main_tab,
        save_main_btn,
        ui_Xmax,
        ui_Xmin,
        ui_Zmax1,
        ui_Zmax2,
        ui_Zmin1,
        ui_Zmin2,
        ui_allcam,
        ui_base_name,
        ui_chfield,
        ui_cn,
        ui_cnx,
        ui_cny,
        ui_corrmin,
        ui_cr_sz,
        ui_csumg,
        ui_disco,
        ui_eps0,
        ui_existing_target,
        ui_gvth,
        ui_hp,
        ui_img_cal,
        ui_img_name,
        ui_imx,
        ui_imy,
        ui_mask_base,
        ui_mask_flag,
        ui_mmp_d,
        ui_mmp_n1,
        ui_mmp_n2,
        ui_mmp_n3,
        ui_nnmax,
        ui_nnmin,
        ui_num_cams,
        ui_nxmax,
        ui_nxmin,
        ui_nymax,
        ui_nymin,
        ui_pix_x,
        ui_pix_y,
        ui_seq_first,
        ui_seq_last,
        ui_splitter,
        ui_sumg,
        ui_tiff,
    )


@app.cell
def _(list_get, mo, params, safe_bool, safe_float, safe_int, sec):
    _cal_ori = sec(params, "cal_ori")
    _detect_plate = sec(params, "detect_plate")
    _man_ori = sec(params, "man_ori")
    _examine = sec(params, "examine")
    _orient = sec(params, "orient")
    _dumbbell = sec(params, "dumbbell")
    _shaking = sec(params, "shaking")

    ui_cal_splitter = mo.ui.checkbox(
        label="Split calibration image into 4?",
        value=safe_bool(_cal_ori.get("cal_splitter"), False),
    )

    _img_cal_name = _cal_ori.get("img_cal_name", [])
    _img_ori = _cal_ori.get("img_ori", [])

    ui_cal_img = [
        mo.ui.text(
            label=f"Calibration image cam {i + 1}",
            value=str(list_get(_img_cal_name, i, "---")),
            full_width=True,
        )
        for i in range(4)
    ]
    ui_ori_img = [
        mo.ui.text(
            label=f"Orientation file cam {i + 1}",
            value=str(list_get(_img_ori, i, "---")),
            full_width=True,
        )
        for i in range(4)
    ]

    ui_fixp = mo.ui.text(
        label="fixp_name",
        value=str(_cal_ori.get("fixp_name", "")),
        full_width=True,
    )

    ui_dp_gv = [
        mo.ui.number(
            label=f"detect_plate gvth_{i + 1}",
            value=safe_int(_detect_plate.get(f"gvth_{i + 1}", 0), 0),
            step=1,
        )
        for i in range(4)
    ]
    ui_dp_tol_dis = mo.ui.number(
        label="tolerable_discontinuity (tol_dis)",
        value=safe_int(_detect_plate.get("tol_dis"), 0),
        step=1,
    )
    ui_dp_min_npix = mo.ui.number(
        label="min_npix", value=safe_int(_detect_plate.get("min_npix"), 0), step=1
    )
    ui_dp_max_npix = mo.ui.number(
        label="max_npix", value=safe_int(_detect_plate.get("max_npix"), 0), step=1
    )
    ui_dp_min_x = mo.ui.number(
        label="min_npix_x",
        value=safe_int(_detect_plate.get("min_npix_x"), 0),
        step=1,
    )
    ui_dp_max_x = mo.ui.number(
        label="max_npix_x",
        value=safe_int(_detect_plate.get("max_npix_x"), 0),
        step=1,
    )
    ui_dp_min_y = mo.ui.number(
        label="min_npix_y",
        value=safe_int(_detect_plate.get("min_npix_y"), 0),
        step=1,
    )
    ui_dp_max_y = mo.ui.number(
        label="max_npix_y",
        value=safe_int(_detect_plate.get("max_npix_y"), 0),
        step=1,
    )
    ui_dp_sum_grey = mo.ui.number(
        label="sum_grey", value=safe_int(_detect_plate.get("sum_grey"), 0), step=1
    )
    ui_dp_size_cross = mo.ui.number(
        label="size_cross",
        value=safe_int(_detect_plate.get("size_cross"), 0),
        step=1,
    )

    _nr = _man_ori.get("nr", [])
    _nr_pad = list(_nr) + [0] * (16 - len(_nr))

    ui_man_ori = []
    for _cam in range(4):
        _row = []
        for _p in range(4):
            _idx = _cam * 4 + _p
            _row.append(
                mo.ui.number(
                    label=f"Cam {_cam + 1} P{_p + 1}",
                    value=safe_int(_nr_pad[_idx], 0),
                    step=1,
                )
            )
        ui_man_ori.append(_row)

    ui_examine = mo.ui.checkbox(
        label="Examine_Flag", value=safe_bool(_examine.get("Examine_Flag"), False)
    )
    ui_combine = mo.ui.checkbox(
        label="Combine_Flag", value=safe_bool(_examine.get("Combine_Flag"), False)
    )

    ui_pnfo = mo.ui.number(
        label="pnfo", value=safe_int(_orient.get("pnfo"), 0), step=1
    )
    ui_cc = mo.ui.checkbox(label="cc", value=safe_bool(_orient.get("cc"), False))
    ui_xh = mo.ui.checkbox(label="xh", value=safe_bool(_orient.get("xh"), False))
    ui_yh = mo.ui.checkbox(label="yh", value=safe_bool(_orient.get("yh"), False))
    ui_k1 = mo.ui.checkbox(label="k1", value=safe_bool(_orient.get("k1"), False))
    ui_k2 = mo.ui.checkbox(label="k2", value=safe_bool(_orient.get("k2"), False))
    ui_k3 = mo.ui.checkbox(label="k3", value=safe_bool(_orient.get("k3"), False))
    ui_p1 = mo.ui.checkbox(label="p1", value=safe_bool(_orient.get("p1"), False))
    ui_p2 = mo.ui.checkbox(label="p2", value=safe_bool(_orient.get("p2"), False))
    ui_scale = mo.ui.checkbox(
        label="scale", value=safe_bool(_orient.get("scale"), False)
    )
    ui_shear = mo.ui.checkbox(
        label="shear", value=safe_bool(_orient.get("shear"), False)
    )
    ui_interf = mo.ui.checkbox(
        label="interf", value=safe_bool(_orient.get("interf"), False)
    )

    ui_sh_first = mo.ui.number(
        label="shaking_first_frame",
        value=safe_int(_shaking.get("shaking_first_frame"), 0),
        step=1,
    )
    ui_sh_last = mo.ui.number(
        label="shaking_last_frame",
        value=safe_int(_shaking.get("shaking_last_frame"), 0),
        step=1,
    )
    ui_sh_max_pts = mo.ui.number(
        label="shaking_max_num_points",
        value=safe_int(_shaking.get("shaking_max_num_points"), 0),
        step=1,
    )
    ui_sh_max_frames = mo.ui.number(
        label="shaking_max_num_frames",
        value=safe_int(_shaking.get("shaking_max_num_frames"), 0),
        step=1,
    )

    ui_db_eps = mo.ui.number(
        label="dumbbell_eps",
        value=safe_float(_dumbbell.get("dumbbell_eps"), 0.0),
        step=0.01,
    )
    ui_db_scale = mo.ui.number(
        label="dumbbell_scale",
        value=safe_float(_dumbbell.get("dumbbell_scale"), 0.0),
        step=0.1,
    )
    ui_db_gd = mo.ui.number(
        label="dumbbell_gradient_descent",
        value=safe_float(_dumbbell.get("dumbbell_gradient_descent"), 0.0),
        step=0.01,
    )
    ui_db_pen = mo.ui.number(
        label="dumbbell_penalty_weight",
        value=safe_float(_dumbbell.get("dumbbell_penalty_weight"), 0.0),
        step=0.1,
    )
    ui_db_step = mo.ui.number(
        label="dumbbell_step",
        value=safe_int(_dumbbell.get("dumbbell_step"), 0),
        step=1,
    )
    ui_db_niter = mo.ui.number(
        label="dumbbell_niter",
        value=safe_int(_dumbbell.get("dumbbell_niter"), 0),
        step=1,
    )

    save_cal_btn = mo.ui.run_button(label="Save Calibration Parameters")

    cal_tab = mo.vstack(
        [
            mo.md("### Calibration images"),
            ui_cal_splitter,
            mo.hstack([mo.vstack(ui_cal_img), mo.vstack(ui_ori_img)], gap=2),
            ui_fixp,
            mo.md("### detect_plate"),
            mo.hstack([mo.vstack(ui_dp_gv[:2]), mo.vstack(ui_dp_gv[2:])], gap=2),
            mo.hstack(
                [
                    ui_dp_tol_dis,
                    ui_dp_min_npix,
                    ui_dp_max_npix,
                    ui_dp_min_x,
                    ui_dp_max_x,
                    ui_dp_min_y,
                    ui_dp_max_y,
                    ui_dp_sum_grey,
                    ui_dp_size_cross,
                ],
                gap=1,
            ),
            mo.md("### Manual pre-orientation (man_ori.nr)"),
            mo.vstack([mo.hstack(row, gap=1) for row in ui_man_ori]),
            mo.md("### Examine"),
            mo.hstack([ui_examine, ui_combine], gap=1),
            mo.md("### Orient"),
            ui_pnfo,
            mo.hstack([ui_cc, ui_xh, ui_yh, ui_interf], gap=1),
            mo.hstack([ui_k1, ui_k2, ui_k3, ui_p1, ui_p2], gap=1),
            mo.hstack([ui_scale, ui_shear], gap=1),
            mo.md("### Shaking"),
            mo.hstack(
                [ui_sh_first, ui_sh_last, ui_sh_max_pts, ui_sh_max_frames], gap=1
            ),
            mo.md("### Dumbbell"),
            mo.hstack(
                [
                    ui_db_eps,
                    ui_db_scale,
                    ui_db_gd,
                    ui_db_pen,
                    ui_db_step,
                    ui_db_niter,
                ],
                gap=1,
            ),
            save_cal_btn,
        ]
    )
    return (
        cal_tab,
        save_cal_btn,
        ui_cal_img,
        ui_cal_splitter,
        ui_cc,
        ui_combine,
        ui_db_eps,
        ui_db_gd,
        ui_db_niter,
        ui_db_pen,
        ui_db_scale,
        ui_db_step,
        ui_dp_gv,
        ui_dp_max_npix,
        ui_dp_max_x,
        ui_dp_max_y,
        ui_dp_min_npix,
        ui_dp_min_x,
        ui_dp_min_y,
        ui_dp_size_cross,
        ui_dp_sum_grey,
        ui_dp_tol_dis,
        ui_examine,
        ui_fixp,
        ui_interf,
        ui_k1,
        ui_k2,
        ui_k3,
        ui_man_ori,
        ui_ori_img,
        ui_p1,
        ui_p2,
        ui_pnfo,
        ui_scale,
        ui_sh_first,
        ui_sh_last,
        ui_sh_max_frames,
        ui_sh_max_pts,
        ui_shear,
        ui_xh,
        ui_yh,
    )


@app.cell
def _(mo, params, safe_bool, safe_float, sec):
    _track = sec(params, "track")

    ui_dvxmin = mo.ui.number(
        label="dvxmin", value=safe_float(_track.get("dvxmin"), 0.0), step=0.1
    )
    ui_dvxmax = mo.ui.number(
        label="dvxmax", value=safe_float(_track.get("dvxmax"), 0.0), step=0.1
    )
    ui_dvymin = mo.ui.number(
        label="dvymin", value=safe_float(_track.get("dvymin"), 0.0), step=0.1
    )
    ui_dvymax = mo.ui.number(
        label="dvymax", value=safe_float(_track.get("dvymax"), 0.0), step=0.1
    )
    ui_dvzmin = mo.ui.number(
        label="dvzmin", value=safe_float(_track.get("dvzmin"), 0.0), step=0.1
    )
    ui_dvzmax = mo.ui.number(
        label="dvzmax", value=safe_float(_track.get("dvzmax"), 0.0), step=0.1
    )

    ui_angle = mo.ui.number(
        label="angle [gon]", value=safe_float(_track.get("angle"), 0.0), step=0.1
    )
    ui_dacc = mo.ui.number(
        label="dacc", value=safe_float(_track.get("dacc"), 0.0), step=0.1
    )
    ui_new = mo.ui.checkbox(
        label="Add new particles?",
        value=safe_bool(_track.get("flagNewParticles"), True),
    )

    save_track_btn = mo.ui.run_button(label="Save Tracking Parameters")

    track_tab = mo.vstack(
        [
            mo.hstack([ui_dvxmin, ui_dvxmax, ui_dvymin, ui_dvymax], gap=1),
            mo.hstack([ui_dvzmin, ui_dvzmax, ui_angle, ui_dacc], gap=1),
            ui_new,
            save_track_btn,
        ]
    )
    return (
        save_track_btn,
        track_tab,
        ui_angle,
        ui_dacc,
        ui_dvxmax,
        ui_dvxmin,
        ui_dvymax,
        ui_dvymin,
        ui_dvzmax,
        ui_dvzmin,
        ui_new,
    )


@app.cell
def _(cal_tab, main_tab, mo, track_tab):
    tabs = mo.ui.tabs(
        {"Main": main_tab, "Calibration": cal_tab, "Tracking": track_tab}
    )
    tabs
    return


@app.cell
def _(
    exp,
    mo,
    pm,
    save_cal_btn,
    save_main_btn,
    save_track_btn,
    ui_Xmax,
    ui_Xmin,
    ui_Zmax1,
    ui_Zmax2,
    ui_Zmin1,
    ui_Zmin2,
    ui_allcam,
    ui_angle,
    ui_base_name,
    ui_cal_img,
    ui_cal_splitter,
    ui_cc,
    ui_chfield,
    ui_cn,
    ui_cnx,
    ui_cny,
    ui_combine,
    ui_corrmin,
    ui_cr_sz,
    ui_csumg,
    ui_dacc,
    ui_db_eps,
    ui_db_gd,
    ui_db_niter,
    ui_db_pen,
    ui_db_scale,
    ui_db_step,
    ui_disco,
    ui_dp_gv,
    ui_dp_max_npix,
    ui_dp_max_x,
    ui_dp_max_y,
    ui_dp_min_npix,
    ui_dp_min_x,
    ui_dp_min_y,
    ui_dp_size_cross,
    ui_dp_sum_grey,
    ui_dp_tol_dis,
    ui_dvxmax,
    ui_dvxmin,
    ui_dvymax,
    ui_dvymin,
    ui_dvzmax,
    ui_dvzmin,
    ui_eps0,
    ui_examine,
    ui_existing_target,
    ui_fixp,
    ui_gvth,
    ui_hp,
    ui_img_cal,
    ui_img_name,
    ui_imx,
    ui_imy,
    ui_interf,
    ui_k1,
    ui_k2,
    ui_k3,
    ui_man_ori,
    ui_mask_base,
    ui_mask_flag,
    ui_mmp_d,
    ui_mmp_n1,
    ui_mmp_n2,
    ui_mmp_n3,
    ui_new,
    ui_nnmax,
    ui_nnmin,
    ui_num_cams,
    ui_nxmax,
    ui_nxmin,
    ui_nymax,
    ui_nymin,
    ui_ori_img,
    ui_p1,
    ui_p2,
    ui_pix_x,
    ui_pix_y,
    ui_pnfo,
    ui_scale,
    ui_seq_first,
    ui_seq_last,
    ui_sh_first,
    ui_sh_last,
    ui_sh_max_frames,
    ui_sh_max_pts,
    ui_shear,
    ui_splitter,
    ui_sumg,
    ui_tiff,
    ui_xh,
    ui_yh,
):
    def _ensure_section(name):
        if name not in exp.pm.parameters or not isinstance(
            exp.pm.parameters.get(name), dict
        ):
            exp.pm.parameters[name] = {}
        return exp.pm.parameters[name]


    messages = []

    if save_main_btn.value:
        n = int(ui_num_cams.value)
        exp.pm.parameters["num_cams"] = n
        pm.num_cams = n

        _ptv_sec = _ensure_section("ptv")
        _ptv_sec.update(
            {
                "img_name": [w.value for w in ui_img_name][:n],
                "img_cal": [w.value for w in ui_img_cal][:n],
                "hp_flag": bool(ui_hp.value),
                "allcam_flag": bool(ui_allcam.value),
                "tiff_flag": bool(ui_tiff.value),
                "imx": int(ui_imx.value),
                "imy": int(ui_imy.value),
                "pix_x": float(ui_pix_x.value),
                "pix_y": float(ui_pix_y.value),
                "chfield": int(ui_chfield.value),
                "mmp_n1": float(ui_mmp_n1.value),
                "mmp_n2": float(ui_mmp_n2.value),
                "mmp_n3": float(ui_mmp_n3.value),
                "mmp_d": float(ui_mmp_d.value),
                "splitter": bool(ui_splitter.value),
            }
        )

        _targ_rec_sec = _ensure_section("targ_rec")
        _targ_rec_sec.update(
            {
                "gvthres": [int(w.value) for w in ui_gvth][:n],
                "disco": int(ui_disco.value),
                "nnmin": int(ui_nnmin.value),
                "nnmax": int(ui_nnmax.value),
                "nxmin": int(ui_nxmin.value),
                "nxmax": int(ui_nxmax.value),
                "nymin": int(ui_nymin.value),
                "nymax": int(ui_nymax.value),
                "sumg_min": int(ui_sumg.value),
                "cr_sz": int(ui_cr_sz.value),
            }
        )

        _pft_version_sec = _ensure_section("pft_version")
        _pft_version_sec["Existing_Target"] = int(bool(ui_existing_target.value))

        _seq_sec = _ensure_section("sequence")
        _seq_sec.update(
            {
                "base_name": [w.value for w in ui_base_name][:n],
                "first": int(ui_seq_first.value),
                "last": int(ui_seq_last.value),
            }
        )

        _criteria_sec = _ensure_section("criteria")
        _criteria_sec.update(
            {
                "X_lay": [int(ui_Xmin.value), int(ui_Xmax.value)],
                "Zmin_lay": [int(ui_Zmin1.value), int(ui_Zmin2.value)],
                "Zmax_lay": [int(ui_Zmax1.value), int(ui_Zmax2.value)],
                "cnx": float(ui_cnx.value),
                "cny": float(ui_cny.value),
                "cn": float(ui_cn.value),
                "csumg": float(ui_csumg.value),
                "corrmin": float(ui_corrmin.value),
                "eps0": float(ui_eps0.value),
            }
        )

        _masking_sec = _ensure_section("masking")
        _masking_sec.update(
            {
                "mask_flag": bool(ui_mask_flag.value),
                "mask_base_name": ui_mask_base.value,
            }
        )

        exp.save_parameters()
        messages.append("✅ Saved Main parameters")

    if save_cal_btn.value:
        n = int(exp.pm.parameters.get("num_cams", pm.num_cams or 0) or 0)

        _ptv_sec2 = _ensure_section("ptv")
        _ptv_sec2.update(
            {
                "imx": int(ui_imx.value),
                "imy": int(ui_imy.value),
                "pix_x": float(ui_pix_x.value),
                "pix_y": float(ui_pix_y.value),
            }
        )

        _cal_ori_sec = _ensure_section("cal_ori")
        _cal_ori_sec.update(
            {
                "fixp_name": ui_fixp.value,
                "img_cal_name": [w.value for w in ui_cal_img][:n],
                "img_ori": [w.value for w in ui_ori_img][:n],
                "cal_splitter": bool(ui_cal_splitter.value),
            }
        )

        _detect_plate_sec = _ensure_section("detect_plate")
        _detect_plate_sec.update(
            {
                "gvth_1": int(ui_dp_gv[0].value),
                "gvth_2": int(ui_dp_gv[1].value),
                "gvth_3": int(ui_dp_gv[2].value),
                "gvth_4": int(ui_dp_gv[3].value),
                "tol_dis": int(ui_dp_tol_dis.value),
                "min_npix": int(ui_dp_min_npix.value),
                "max_npix": int(ui_dp_max_npix.value),
                "min_npix_x": int(ui_dp_min_x.value),
                "max_npix_x": int(ui_dp_max_x.value),
                "min_npix_y": int(ui_dp_min_y.value),
                "max_npix_y": int(ui_dp_max_y.value),
                "sum_grey": int(ui_dp_sum_grey.value),
                "size_cross": int(ui_dp_size_cross.value),
            }
        )

        _man_ori_sec = _ensure_section("man_ori")
        _nr_list = []
        for _cam in range(4):
            for _p in range(4):
                _nr_list.append(int(ui_man_ori[_cam][_p].value))
        _man_ori_sec["nr"] = _nr_list

        _examine_sec = _ensure_section("examine")
        _examine_sec.update(
            {
                "Examine_Flag": bool(ui_examine.value),
                "Combine_Flag": bool(ui_combine.value),
            }
        )

        _orient_sec = _ensure_section("orient")
        _orient_sec.update(
            {
                "pnfo": int(ui_pnfo.value),
                "cc": int(bool(ui_cc.value)),
                "xh": int(bool(ui_xh.value)),
                "yh": int(bool(ui_yh.value)),
                "k1": int(bool(ui_k1.value)),
                "k2": int(bool(ui_k2.value)),
                "k3": int(bool(ui_k3.value)),
                "p1": int(bool(ui_p1.value)),
                "p2": int(bool(ui_p2.value)),
                "scale": int(bool(ui_scale.value)),
                "shear": int(bool(ui_shear.value)),
                "interf": int(bool(ui_interf.value)),
            }
        )

        _shaking_sec = _ensure_section("shaking")
        _shaking_sec.update(
            {
                "shaking_first_frame": int(ui_sh_first.value),
                "shaking_last_frame": int(ui_sh_last.value),
                "shaking_max_num_points": int(ui_sh_max_pts.value),
                "shaking_max_num_frames": int(ui_sh_max_frames.value),
            }
        )

        _dumbbell_sec = _ensure_section("dumbbell")
        _dumbbell_sec.update(
            {
                "dumbbell_eps": float(ui_db_eps.value),
                "dumbbell_scale": float(ui_db_scale.value),
                "dumbbell_gradient_descent": float(ui_db_gd.value),
                "dumbbell_penalty_weight": float(ui_db_pen.value),
                "dumbbell_step": int(ui_db_step.value),
                "dumbbell_niter": int(ui_db_niter.value),
            }
        )

        exp.save_parameters()
        messages.append("✅ Saved Calibration parameters")

    if save_track_btn.value:
        _track_sec = _ensure_section("track")
        _track_sec.update(
            {
                "dvxmin": float(ui_dvxmin.value),
                "dvxmax": float(ui_dvxmax.value),
                "dvymin": float(ui_dvymin.value),
                "dvymax": float(ui_dvymax.value),
                "dvzmin": float(ui_dvzmin.value),
                "dvzmax": float(ui_dvzmax.value),
                "angle": float(ui_angle.value),
                "dacc": float(ui_dacc.value),
                "flagNewParticles": bool(ui_new.value),
            }
        )
        exp.save_parameters()
        messages.append("✅ Saved Tracking parameters")

    status = mo.md("\n\n".join(messages)) if messages else mo.md("")
    status
    return


if __name__ == "__main__":
    app.run()
