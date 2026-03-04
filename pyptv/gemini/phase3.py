import numpy as np
from scipy.spatial.transform import Rotation as R_scipy

# --- SENSOR CONSTANTS ---
PIXEL_SIZE_MM = 0.005  # 5 microns
IMAGE_WIDTH = 2560
IMAGE_HEIGHT = 2048
NUM_CAMERAS = 4

def phase3_convert_to_openptv(intrinsics, extrinsics_world_to_cam):
    """
    Converts OpenCV intrinsic/extrinsic matrices into OpenPTV physical parameters:
    - Camera physical position in 3D (X0, Y0, Z0) in mm.
    - Euler angles (Omega, Phi, Kappa) in radians.
    - Focal length (c) in mm.
    - Principal point offset (xp, yp) in mm.
    """
    openptv_params = {}
    
    # Calculate the exact center of the sensor in pixels
    sensor_center_x = IMAGE_WIDTH / 2.0
    sensor_center_y = IMAGE_HEIGHT / 2.0

    print("Phase 3: Converting OpenCV to Physical OpenPTV Parameters...\n")

    for cam_id in range(NUM_CAMERAS):
        # ---------------------------------------------------------
        # 1. INTRINSICS (Pixels to Millimeters)
        # ---------------------------------------------------------
        K = intrinsics[cam_id]['K']
        D = intrinsics[cam_id]['D'].flatten()
        
        # Extract OpenCV focal lengths and principal point in pixels
        fx_pix = K[0, 0]
        fy_pix = K[1, 1]
        cx_pix = K[0, 2]
        cy_pix = K[1, 2]
        
        # Average the focal lengths (assuming square pixels) and convert to mm
        focal_length_mm = ((fx_pix + fy_pix) / 2.0) * PIXEL_SIZE_MM
        
        # Convert Principal Point to mm offset from the sensor center
        # (OpenPTV origin is the center of the sensor, OpenCV is top-left)
        xp_mm = (cx_pix - sensor_center_x) * PIXEL_SIZE_MM
        yp_mm = (cy_pix - sensor_center_y) * PIXEL_SIZE_MM
        
        # ---------------------------------------------------------
        # 2. EXTRINSICS (Camera Position in World Frame)
        # ---------------------------------------------------------
        R_cv = extrinsics_world_to_cam[cam_id]['R']
        T_cv = extrinsics_world_to_cam[cam_id]['T']
        
        # OpenCV T vector is the position of the WORLD relative to the CAMERA.
        # OpenPTV wants the position of the CAMERA relative to the WORLD (C).
        # Formula: C = -R^T * T
        R_inv = R_cv.T
        camera_center = -np.dot(R_inv, T_cv)
        X0, Y0, Z0 = camera_center.flatten()
        
        # ---------------------------------------------------------
        # 3. EULER ANGLES (Omega, Phi, Kappa)
        # ---------------------------------------------------------
        # OpenPTV usually decomposes the rotation matrix into three successive 
        # rotations. To keep our custom Bundle Adjustment mathematically sound 
        # and reversible, we use standard extrinsic xyz Euler angles.
        # R_scipy uses standard aerospace/robotics conventions.
        rotation_obj = R_scipy.from_matrix(R_cv)
        omega, phi, kappa = rotation_obj.as_euler('xyz', degrees=False)
        
        # ---------------------------------------------------------
        # Store in pyPTV-like dictionary
        # ---------------------------------------------------------
        openptv_params[cam_id] = {
            # Extrinsics
            'x0': X0, 'y0': Y0, 'z0': Z0,
            'omega': omega, 'phi': phi, 'kappa': kappa,
            # Intrinsics
            'c': focal_length_mm, 
            'xp': xp_mm, 'yp': yp_mm,
            # Radial & Decentering Distortion (leaving in OpenCV format for BA)
            'k1': D[0] if len(D) > 0 else 0.0,
            'k2': D[1] if len(D) > 1 else 0.0,
            'p1': D[2] if len(D) > 2 else 0.0,
            'p2': D[3] if len(D) > 3 else 0.0,
            'k3': D[4] if len(D) > 4 else 0.0
        }

        # Print out the results for sanity check
        print(f"--- Camera {cam_id} ---")
        print(f"  Position (mm): X0 = {X0:7.1f}, Y0 = {Y0:7.1f}, Z0 = {Z0:7.1f}")
        print(f"  Euler (deg):   w  = {np.degrees(omega):7.1f}, p = {np.degrees(phi):7.1f}, k = {np.degrees(kappa):7.1f}")
        print(f"  Focal (mm):    c  = {focal_length_mm:.3f}")
        print(f"  Principal pt:  xp = {xp_mm:.4f} mm, yp = {yp_mm:.4f} mm\n")

    return openptv_params

# ====================================================================
# Execution Context
# ====================================================================
if __name__ == "__main__":
    # Mock data to simulate execution if run isolated
    # openptv_params = phase3_convert_to_openptv(intrinsics, extrinsics_world_to_cam)
    pass