import numpy as np
from scipy.optimize import least_squares

# --- OpenPTV Python Imports ---
from openptv_python.calibration import Calibration
from openptv_python.multimed import MultimediaPar
from openptv_python.imgcoord import img_coord
from openptv_python.trafo import pixel_to_metric
from openptv_python.parameters import ControlPar

# --- CONSTANTS ---
PIXEL_SIZE_MM = 0.005
IMAGE_WIDTH = 2560
IMAGE_HEIGHT = 2048
GRID_COLS = 7
GRID_ROWS = 6
NUM_DOTS = GRID_COLS * GRID_ROWS
DOT_SPACING_MM = 120.0
NUM_CAMERAS = 4

# --- WEIGHTS FOR SOFT CONSTRAINTS ---
LAMBDA_REPROJ = 1.0  # Weight for 1 pixel of error
LAMBDA_PLANE  = 50.0 # Weight for 1 mm of out-of-plane error
LAMBDA_DIST   = 50.0 # Weight for 1 mm of length error

# ====================================================================
# 1. HELPER: GEOMETRY & OpenPTV CONTEXT
# ====================================================================
def get_adjacent_dot_pairs(cols, rows):
    """Generates index pairs for adjacent dots (horizontal and vertical)"""
    pairs =[]
    for r in range(rows):
        for c in range(cols):
            idx = r * cols + c
            if c < cols - 1:     # Right neighbor
                pairs.append((idx, idx + 1))
            if r < rows - 1:     # Bottom neighbor
                pairs.append((idx, idx + cols))
    return pairs

def get_openptv_context():
    """Sets up the Control and Multimedia parameters for OpenPTV."""
    cpar = ControlPar()
    # Note: openptv-python API usually uses methods or direct attribute access
    # We set image size in pixels and pixel dimensions in mm
    cpar.set_image_size((IMAGE_WIDTH, IMAGE_HEIGHT))
    cpar.set_pixel_size((PIXEL_SIZE_MM, PIXEL_SIZE_MM))
    
    # Standard Air calibration (refractive index = 1.0)
    mmp = MultimediaPar(n1=1.0, n2=[1.0], n3=1.0, d=[0.0])
    return cpar, mmp

def convert_pixels_to_metric(points_2d_pixels, cpar):
    """
    Converts raw 2D pixel coordinates (top-left origin) to OpenPTV's 
    metric sensor coordinates (mm, centered origin).
    """
    points_2d_metric = {cam_id: {} for cam_id in points_2d_pixels.keys()}
    
    for cam_id, frames in points_2d_pixels.items():
        for frame_idx, pts in frames.items():
            pts_metric =[]
            for pt in pts:
                # OpenPTV pixel_to_metric maps Top-Left pixels to Center-Origin mm
                x_mm, y_mm = pixel_to_metric(pt[0], pt[1], cpar)
                pts_metric.append([x_mm, y_mm])
            points_2d_metric[cam_id][frame_idx] = np.array(pts_metric)
            
    return points_2d_metric

# ====================================================================
# 2. STATE PACKING / UNPACKING FOR SCIPY
# ====================================================================
def pack_state(calibrations_dict, points_3d):
    """Flattens OpenPTV calibrations and 3D points into a 1D array."""
    camera_params_list =[]
    for cam_id in range(NUM_CAMERAS):
        cal = calibrations_dict[cam_id]
        cam_array =[
            cal.ext_par.x0, cal.ext_par.y0, cal.ext_par.z0,
            cal.ext_par.omega, cal.ext_par.phi, cal.ext_par.kappa,
            cal.int_par.cc, cal.int_par.xh, cal.int_par.yh,
            cal.added_par.k1, cal.added_par.k2, cal.added_par.p1, 
            cal.added_par.p2, cal.added_par.k3
        ]
        camera_params_list.append(cam_array)
    
    cam_array_1d = np.array(camera_params_list).flatten()
    pts_array_1d = points_3d.flatten()
    return np.hstack((cam_array_1d, pts_array_1d))

def unpack_state_to_openptv(state, num_frames):
    """Rebuilds OpenPTV Calibration objects and 3D points from 1D array."""
    calibrations =[]
    cam_data = state[:NUM_CAMERAS * 14].reshape((NUM_CAMERAS, 14))
    pts_data = state[NUM_CAMERAS * 14:].reshape((num_frames, NUM_DOTS, 3))
    
    for cam_id in range(NUM_CAMERAS):
        cal = Calibration()
        
        # Extrinsics (Pos & Angles)
        cal.ext_par.x0, cal.ext_par.y0, cal.ext_par.z0 = cam_data[cam_id, 0:3]
        cal.ext_par.omega, cal.ext_par.phi, cal.ext_par.kappa = cam_data[cam_id, 3:6]
        
        # Intrinsics (Focal length & Principal Point offset)
        cal.int_par.cc = cam_data[cam_id, 6]
        cal.int_par.xh = cam_data[cam_id, 7]
        cal.int_par.yh = cam_data[cam_id, 8]
        
        # Distortion (Radial & Decentering)
        cal.added_par.k1 = cam_data[cam_id, 9]
        cal.added_par.k2 = cam_data[cam_id, 10]
        cal.added_par.p1 = cam_data[cam_id, 11]
        cal.added_par.p2 = cam_data[cam_id, 12]
        cal.added_par.k3 = cam_data[cam_id, 13]
        
        # OpenPTV requires the rotation matrix to be updated after angles change
        cal.ext_par.update_rotation_matrix()
        
        calibrations.append(cal)
        
    return calibrations, pts_data

# ====================================================================
# 3. THE OpenPTV OBJECTIVE (RESIDUAL) FUNCTION
# ====================================================================
def openptv_bundle_adjustment_objective(state, num_frames, points_2d_metric, sync_frames, pair_indices, mmp):
    """
    Computes residuals using strictly OpenPTV's internal 3D->2D metric projection math.
    """
    calibrations, points_3d = unpack_state_to_openptv(state, num_frames)
    residuals =[]
    
    # --- A. Reprojection Error (Using OpenPTV img_coord) ---
    for cam_id in range(NUM_CAMERAS):
        cal = calibrations[cam_id]
        
        for f_idx, frame in enumerate(sync_frames):
            pts_3d = points_3d[f_idx]
            observed_metric = points_2d_metric[cam_id][frame]
            
            for pt_idx, p3d in enumerate(pts_3d):
                # Core OpenPTV function: 3D to 2D metric sensor space
                proj_x_mm, proj_y_mm = img_coord(p3d, cal, mmp)
                
                obs_x_mm, obs_y_mm = observed_metric[pt_idx]
                
                # Difference in mm on the sensor
                err_x_mm = proj_x_mm - obs_x_mm
                err_y_mm = proj_y_mm - obs_y_mm
                
                # Convert mm error back to "pixels" mathematically 
                # so LAMBDA_REPROJ behaves intuitively (e.g. 1 unit = 1 pixel)
                err_x_pix = err_x_mm / PIXEL_SIZE_MM
                err_y_pix = err_y_mm / PIXEL_SIZE_MM
                
                residuals.extend([err_x_pix * LAMBDA_REPROJ, err_y_pix * LAMBDA_REPROJ])
                
    # --- B. Soft Constraint: Planarity (3D Millimeters) ---
    for f_idx in range(num_frames):
        pts_3d = points_3d[f_idx]
        centroid = np.mean(pts_3d, axis=0)
        centered_pts = pts_3d - centroid
        
        # SVD finds the best-fit plane (normal vector corresponds to smallest singular value)
        _, _, V = np.linalg.svd(centered_pts)
        plane_normal = V[2, :] 
        
        distances_to_plane = np.dot(centered_pts, plane_normal)
        residuals.extend(distances_to_plane * LAMBDA_PLANE)
        
    # --- C. Soft Constraint: Inter-dot Distance (3D Millimeters) ---
    for f_idx in range(num_frames):
        pts_3d = points_3d[f_idx]
        
        pt_A = pts_3d[[p[0] for p in pair_indices]]
        pt_B = pts_3d[[p[1] for p in pair_indices]]
        
        distances = np.linalg.norm(pt_A - pt_B, axis=1)
        error_dist = distances - DOT_SPACING_MM
        residuals.extend(error_dist * LAMBDA_DIST)

    return np.array(residuals)

# ====================================================================
# 4. EXECUTION WRAPPER
# ====================================================================
def run_openptv_bundle_adjustment(points_2d_pixels, sync_frames, initial_calibrations, points_3d_initial):
    """
    Main Runner. 
    `initial_calibrations` is a dict of OpenPTV Calibration objects (from Phase 3).
    `points_3d_initial` is the numpy array of 3D point guesses (from Phase 3/OpenCV PnP).
    """
    print("\nPhase 4: Setting up OpenPTV Bundle Adjustment...")
    cpar, mmp = get_openptv_context()
    num_frames = len(sync_frames)
    pair_indices = get_adjacent_dot_pairs(GRID_COLS, GRID_ROWS)
    
    # 1. Convert OpenCV Top-Left Pixels to OpenPTV Centered-Metric mm
    print("Converting 2D Pixel Observations to Metric Sensor Coordinates...")
    points_2d_metric = convert_pixels_to_metric(points_2d_pixels, cpar)
    
    # 2. Pack State
    print("Packing State Vector...")
    initial_state = pack_state(initial_calibrations, points_3d_initial)
    
    # Calculate initial error purely for logging
    initial_residuals = openptv_bundle_adjustment_objective(
        initial_state, num_frames, points_2d_metric, sync_frames, pair_indices, mmp
    )
    print(f"Initial Mean Squared Error: {np.mean(initial_residuals**2):.4f}")
    
    # 3. Optimize
    print("\nRunning Least Squares Optimization (Levenberg-Marquardt / Trust Region)...")
    result = least_squares(
        openptv_bundle_adjustment_objective, 
        initial_state, 
        method='trf', 
        ftol=1e-5, 
        xtol=1e-5, 
        args=(num_frames, points_2d_metric, sync_frames, pair_indices, mmp)
    )
    
    print(f"Optimization Status: {result.message}")
    print(f"Final Mean Squared Error: {np.mean(result.fun**2):.4f}")
    
    # 4. Unpack optimized results
    optimized_calibrations, optimized_points_3d = unpack_state_to_openptv(result.x, num_frames)
    
    # Write optimized calibrations back to disk (optional but recommended)
    for cam_id, cal in enumerate(optimized_calibrations):
        cal.write(f"cam{cam_id}_optimized.ori", f"cam{cam_id}_optimized.addpar")
        print(f"\n--- Optimized Cam {cam_id} ---")
        print(f"  Pos: X={cal.ext_par.x0:.1f}, Y={cal.ext_par.y0:.1f}, Z={cal.ext_par.z0:.1f} mm")
        print(f"  Focal: c={cal.int_par.cc:.3f} mm")
        
    return optimized_calibrations, optimized_points_3d

# ====================================================================
# Execution Context
# ====================================================================
if __name__ == "__main__":
    # Mock call (requires variables from phases 1-3)
    # opt_cals, opt_3d = run_openptv_bundle_adjustment(points_2d, sync_frames, initial_calibrations, points_3d_init)
    pass