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
NUM_CAMERAS = 4
DUMBBELL_LENGTH_MM = 1000.0
TOLERANCE_MM = 5.0

# ====================================================================
# 1. OpenPTV CONTEXT
# ====================================================================
def get_openptv_context():
    cpar = ControlPar()
    cpar.set_image_size((IMAGE_WIDTH, IMAGE_HEIGHT))
    cpar.set_pixel_size((PIXEL_SIZE_MM, PIXEL_SIZE_MM))
    mmp = MultimediaPar(n1=1.0, n2=[1.0], n3=1.0, d=[0.0])
    return cpar, mmp

def convert_pixel_to_metric_single(pt_2d, cpar):
    """Converts a single (x, y) pixel coordinate to mm sensor coordinate."""
    return pixel_to_metric(pt_2d[0], pt_2d[1], cpar)

# ====================================================================
# 2. RIGOROUS OpenPTV TRIANGULATION (Multi-Camera Ray Intersection)
# ====================================================================
def point_triangulation_objective(pt_3d, metric_observations, calibrations, mmp):
    """
    Calculates the 2D metric reprojection error for a single 3D point 
    across all cameras that saw it.
    """
    residuals =[]
    for cam_id, obs_metric in metric_observations.items():
        cal = calibrations[cam_id]
        
        # Project 3D guess to 2D metric space
        proj_x_mm, proj_y_mm = img_coord(pt_3d, cal, mmp)
        
        # Calculate error in mm
        err_x = proj_x_mm - obs_metric[0]
        err_y = proj_y_mm - obs_metric[1]
        
        residuals.extend([err_x, err_y])
        
    return np.array(residuals)

def triangulate_3d_point(pixel_observations, calibrations, cpar, mmp, initial_guess):
    """
    Finds the optimal 3D coordinate (X,Y,Z) that minimizes reprojection 
    error for a set of 2D pixel observations.
    """
    metric_observations = {}
    for cam_id, pt_2d in pixel_observations.items():
        metric_observations[cam_id] = convert_pixel_to_metric_single(pt_2d, cpar)
        
    # Optimize the 3D point position
    result = least_squares(
        point_triangulation_objective,
        initial_guess,
        method='lm', # Levenberg-Marquardt is fast for small 3-variable problems
        args=(metric_observations, calibrations, mmp)
    )
    
    return result.x, result.fun

# ====================================================================
# 3. DUMBBELL VALIDATION RUNNER
# ====================================================================
def phase5_validate_dumbbell(dumbbell_points_2d, sync_frames, optimized_calibrations):
    """
    dumbbell_points_2d structure: 
    dict: cam_id -> { frame_idx -> [ (x_A, y_A), (x_B, y_B) ] }
    """
    print(f"\nPhase 5: Validating Calibration with {DUMBBELL_LENGTH_MM}mm Dumbbell...")
    cpar, mmp = get_openptv_context()
    
    # We need a rough starting guess for the 3D points.
    # Assuming the setup looks towards Z=0, we start the optimizer at the origin.
    rough_guess_A = np.array([0.0, 0.0, 0.0])
    rough_guess_B = np.array([0.0, 0.0, 0.0])
    
    calculated_distances =[]
    
    for f_idx in sync_frames:
        # Gather observations for Point A and Point B across all cameras
        obs_A = {cam_id: dumbbell_points_2d[cam_id][f_idx][0] for cam_id in range(NUM_CAMERAS)}
        obs_B = {cam_id: dumbbell_points_2d[cam_id][f_idx][1] for cam_id in range(NUM_CAMERAS)}
        
        # Triangulate
        pt_3d_A, res_A = triangulate_3d_point(obs_A, optimized_calibrations, cpar, mmp, rough_guess_A)
        pt_3d_B, res_B = triangulate_3d_point(obs_B, optimized_calibrations, cpar, mmp, rough_guess_B)
        
        # Update our guess for the next frame (since the dumbbell moves continuously, 
        # the previous frame's position is a great guess for the current frame)
        rough_guess_A = pt_3d_A
        rough_guess_B = pt_3d_B
        
        # Calculate 3D Euclidean distance
        distance = np.linalg.norm(pt_3d_A - pt_3d_B)
        calculated_distances.append(distance)
        
    # --- STATISTICS ---
    calculated_distances = np.array(calculated_distances)
    errors = calculated_distances - DUMBBELL_LENGTH_MM
    
    mean_dist = np.mean(calculated_distances)
    std_dev = np.std(calculated_distances)
    rmse = np.sqrt(np.mean(errors**2))
    max_error = np.max(np.abs(errors))
    
    print("-" * 50)
    print("DUMBBELL VALIDATION RESULTS")
    print("-" * 50)
    print(f"Frames Analyzed:      {len(sync_frames)}")
    print(f"Ground Truth Length:  {DUMBBELL_LENGTH_MM:.2f} mm")
    print(f"Measured Mean Length: {mean_dist:.2f} mm")
    print(f"Standard Deviation:   {std_dev:.3f} mm")
    print(f"Max Absolute Error:   {max_error:.3f} mm")
    print(f"RMSE (Root Mean Sq):  {rmse:.3f} mm")
    print("-" * 50)
    
    if rmse <= TOLERANCE_MM:
        print(f"SUCCESS: The RMSE ({rmse:.3f} mm) is within the expected manufacturing tolerance ({TOLERANCE_MM} mm).")
        print("Your OpenPTV camera setup is rigorously calibrated and ready for 3D PTV tracking.")
    else:
        print(f"WARNING: The RMSE ({rmse:.3f} mm) exceeds the tolerance ({TOLERANCE_MM} mm).")
        print("Check your target detection (Phase 1) or optimization weights (Phase 4).")
        
    return calculated_distances, rmse

# ====================================================================
# Execution Context
# ====================================================================
if __name__ == "__main__":
    # Mock usage:
    # 1. Load optimized calibrations from disk
    # cals =[Calibration(), Calibration(), Calibration(), Calibration()]
    # for i in range(4): cals[i].read(f"cam{i}_optimized.ori", f"cam{i}_optimized.addpar")
    
    # 2. Extract dumbbell points using cv2 (similar to Phase 1, but finding 2 bright dots)
    # dumbbell_points_2d = extract_dumbbell_2d("data/dumbbell/")
    
    # 3. Run Validation
    # dists, error = phase5_validate_dumbbell(dumbbell_points_2d, sync_frames, cals)
    pass