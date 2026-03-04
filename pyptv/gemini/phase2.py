import cv2
import numpy as np

# --- GRID PHYSICAL SETTINGS ---
GRID_COLS = 7
GRID_ROWS = 6
DOT_SPACING_MM = 120.0  # 120 mm between dots
IMAGE_SIZE = (2560, 2048)
NUM_CAMERAS = 4

def create_object_points():
    """
    Creates the 3D coordinates of the 7x6 grid in its own local coordinate system.
    Z is perfectly 0 for all points since it's a flat planar surface.
    """
    objp = np.zeros((GRID_COLS * GRID_ROWS, 3), np.float32)
    # Create an active grid of (x, y, 0) scaled by the 120mm physical distance
    mgrid = np.mgrid[0:GRID_COLS, 0:GRID_ROWS].T.reshape(-1, 2)
    objp[:, :2] = mgrid * DOT_SPACING_MM
    return objp

def phase2_initial_calibration(points_2d, sync_frames, origin_frame_idx=30):
    """
    Performs intrinsic and stereo calibration, and sets the global world coordinate
    system based on the grid's location in `origin_frame_idx`.
    """
    if origin_frame_idx not in sync_frames:
        print(f"Warning: Frame {origin_frame_idx} is not in the synchronized frames.")
        print(f"Defaulting to the first available frame: {sync_frames[0]}")
        origin_frame_idx = sync_frames[0]

    objp_single = create_object_points()
    
    # We need the same object points array duplicated for every successful frame
    objpoints =[objp_single for _ in sync_frames]

    # Dictionaries to store the results
    intrinsics = {}
    extrinsics_world_to_cam = {}

    # ---------------------------------------------------------
    # STEP 1: Independent Intrinsic Calibration for Each Camera
    # ---------------------------------------------------------
    print("Step 1: Calibrating Intrinsics...")
    for cam_id in range(NUM_CAMERAS):
        imgpoints = [points_2d[cam_id][f] for f in sync_frames]
        
        # Calibrate camera using all synchronized frames
        ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(
            objpoints, imgpoints, IMAGE_SIZE, None, None
        )
        intrinsics[cam_id] = {
            'K': mtx,       # 3x3 Camera Matrix (focal lengths and principal points)
            'D': dist,      # Distortion coefficients
            'RMS': ret      # Reprojection error in pixels
        }
        print(f"  Cam {cam_id} Intrinsics RMS Error: {ret:.3f} pixels")

    # ---------------------------------------------------------
    # STEP 2: Stereo Calibration (Cam 1, 2, 3 relative to Cam 0)
    # ---------------------------------------------------------
    print("\nStep 2: Stereo Calibrating against Camera 0...")
    stereo_transforms = {0: {'R': np.eye(3), 'T': np.zeros((3, 1))}} # Cam 0 is identity to itself
    
    imgpoints_cam0 = [points_2d[0][f] for f in sync_frames]
    
    # OpenCV stereo calibration flags: we freeze the intrinsics we just found
    flags = cv2.CALIB_FIX_INTRINSIC

    for cam_id in range(1, NUM_CAMERAS):
        imgpoints_cami = [points_2d[cam_id][f] for f in sync_frames]
        
        ret_stereo, _, _, _, _, R, T, E, F = cv2.stereoCalibrate(
            objpoints, 
            imgpoints_cam0, 
            imgpoints_cami, 
            intrinsics[0]['K'], intrinsics[0]['D'],
            intrinsics[cam_id]['K'], intrinsics[cam_id]['D'],
            IMAGE_SIZE, 
            flags=flags
        )
        # R and T map points from Cam 0 coordinate system to Cam i coordinate system
        stereo_transforms[cam_id] = {'R': R, 'T': T}
        print(f"  Stereo Cam 0 -> Cam {cam_id} RMS Error: {ret_stereo:.3f} pixels")

    # ---------------------------------------------------------
    # STEP 3: Anchor the World Coordinate System to Frame 30
    # ---------------------------------------------------------
    print(f"\nStep 3: Anchoring World Frame to Frame {origin_frame_idx}...")
    
    # Grab the 2D points of the grid seen by Camera 0 exactly at Frame 30
    pts2d_frame30_cam0 = points_2d[0][origin_frame_idx]
    
    # SolvePnP gives the rotation and translation from the 3D Grid -> Camera 0
    success, rvec_world_to_cam0, tvec_world_to_cam0 = cv2.solvePnP(
        objp_single, 
        pts2d_frame30_cam0, 
        intrinsics[0]['K'], 
        intrinsics[0]['D']
    )
    
    if not success:
        raise RuntimeError("SolvePnP failed to find the pose for Camera 0 at the origin frame.")

    # Convert rotation vector to 3x3 rotation matrix
    R_world_to_cam0, _ = cv2.Rodrigues(rvec_world_to_cam0)
    T_world_to_cam0 = tvec_world_to_cam0

    # ---------------------------------------------------------
    # STEP 4: Chain Transforms to get World -> Every Camera
    # ---------------------------------------------------------
    # We now know:
    # 1. World -> Cam 0  (from SolvePnP)
    # 2. Cam 0 -> Cam i  (from Stereo Calibrate)
    # We chain them together to map World -> Cam i directly.
    
    print("Step 4: Calculating absolute camera poses...")
    for cam_id in range(NUM_CAMERAS):
        if cam_id == 0:
            R_world_to_cami = R_world_to_cam0
            T_world_to_cami = T_world_to_cam0
        else:
            R_cam0_to_cami = stereo_transforms[cam_id]['R']
            T_cam0_to_cami = stereo_transforms[cam_id]['T']
            
            # Matrix multiplication to chain the rotations and translations
            # X_cami = R_0->i * (R_W->0 * X_W + T_W->0) + T_0->i
            R_world_to_cami = np.dot(R_cam0_to_cami, R_world_to_cam0)
            T_world_to_cami = np.dot(R_cam0_to_cami, T_world_to_cam0) + T_cam0_to_cami

        # Store the absolute extrinsics
        extrinsics_world_to_cam[cam_id] = {
            'R': R_world_to_cami,
            'T': T_world_to_cami
        }
        
        # Let's print the translation (which is roughly where the world origin 
        # is relative to the camera in mm)
        print(f"  Cam {cam_id} Position (T vector from world): \n"
              f"      X: {T_world_to_cami[0][0]:.1f} mm, "
              f"Y: {T_world_to_cami[1][0]:.1f} mm, "
              f"Z: {T_world_to_cami[2][0]:.1f} mm")

    print("\nPhase 2 Complete! Intrinsic and Extrinsic parameters initialized.")
    return intrinsics, extrinsics_world_to_cam

# ====================================================================
# Execution Context (assuming points_2d and sync_frames from Phase 1)
# ====================================================================
if __name__ == "__main__":
    # Mock data to simulate execution if run isolated
    # points_2d = ... (from Phase 1)
    # sync_frames = ... (from Phase 1)
    
    # intrinsics, extrinsics = phase2_initial_calibration(points_2d, sync_frames, origin_frame_idx=30)
    pass