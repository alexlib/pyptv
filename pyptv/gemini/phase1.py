import cv2
import numpy as np
import glob
import os

# --- HARDWARE & CALIBRATION SETUP ---
GRID_COLS = 7
GRID_ROWS = 6
GRID_SIZE = (GRID_COLS, GRID_ROWS) # 7x6 symmetric grid
NUM_DOTS = GRID_COLS * GRID_ROWS   # 42 dots total

IMAGE_WIDTH = 2560
IMAGE_HEIGHT = 2048
PIXEL_SIZE_MM = 0.005 # 5 microns = 0.005 mm (will be used heavily in Phase 3)

# Number of cameras in the setup
NUM_CAMERAS = 4

def get_blob_detector():
    """
    Configures a blob detector specifically for dark circular dots 
    on a bright background.
    """
    # Setup SimpleBlobDetector parameters
    params = cv2.SimpleBlobDetector_Params()

    # Filter by Color (0 = dark blobs, 255 = bright blobs)
    params.filterByColor = True
    params.blobColor = 0

    # Filter by Area (Adjust these min/max values based on how large 
    # the dots appear in your 2560x2048 images)
    params.filterByArea = True
    params.minArea = 50     # minimum pixels squared
    params.maxArea = 10000  # maximum pixels squared

    # Filter by Circularity
    params.filterByCircularity = True
    params.minCircularity = 0.7 # 1.0 is a perfect circle

    # Filter by Convexity
    params.filterByConvexity = True
    params.minConvexity = 0.8

    # Filter by Inertia (measures how elongated the shape is)
    params.filterByInertia = True
    params.minInertiaRatio = 0.5

    # Create a detector with the parameters
    detector = cv2.SimpleBlobDetector_create(params)
    return detector

def extract_2d_grid_points(base_dir, file_extension="tif"):
    """
    Reads synchronized images from 4 cameras, detects the 7x6 symmetric 
    circle grid, and stores the 2D pixel coordinates.
    
    Assumed folder structure:
    base_dir/
      cam0/ frame_0000.tif, frame_0001.tif, ...
      cam1/ frame_0000.tif, frame_0001.tif, ...
      cam2/ frame_0000.tif, frame_0001.tif, ...
      cam3/ frame_0000.tif, frame_0001.tif, ...
    """
    detector = get_blob_detector()
    
    # Data structure to hold our results:
    # points_2d[camera_id][frame_id] = np.array of shape (42, 2)
    points_2d = {cam_id: {} for cam_id in range(NUM_CAMERAS)}
    
    # We need to know which frames have successful detections across ALL cameras.
    # Bundle adjustment and stereo calibration require synchronized views.
    successful_sync_frames =[]

    # Let's assume camera 0 dictates the list of frame filenames
    cam0_path = os.path.join(base_dir, "cam0", f"*.{file_extension}")
    cam0_files = sorted(glob.glob(cam0_path))
    
    if not cam0_files:
        print(f"Warning: No images found in {cam0_path}")
        return points_2d, successful_sync_frames

    print(f"Starting Phase 1: Detecting 7x6 dots in {len(cam0_files)} frames...")

    for frame_idx, filepath in enumerate(cam0_files):
        filename = os.path.basename(filepath)
        
        frame_success = True
        frame_points = {}

        # Check this specific frame across all 4 cameras
        for cam_id in range(NUM_CAMERAS):
            img_path = os.path.join(base_dir, f"cam{cam_id}", filename)
            
            if not os.path.exists(img_path):
                print(f"[Frame {frame_idx}] Missing image for Cam {cam_id}")
                frame_success = False
                break
                
            # Read image in grayscale
            gray = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
            if gray is None:
                print(f"  [Frame {frame_idx}] Failed to load {img_path}")
                frame_success = False
                break

            # Detect the symmetric circular grid
            # ret is a boolean indicating if the exact grid (42 points) was found
            # centers is an array of shape (42, 1, 2) containing (x,y) pixel coordinates
            ret, centers = cv2.findCirclesGrid(
                gray, 
                GRID_SIZE, 
                flags=cv2.CALIB_CB_SYMMETRIC_GRID, 
                blobDetector=detector
            )

            if ret:
                # Squeeze the array from (42, 1, 2) to (42, 2) for easier math later
                centers = centers.squeeze()
                
                # Optional: Refine center detection to sub-pixel accuracy
                # Sub-pixel targeting is critical for OpenPTV accuracy.
                criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
                centers = cv2.cornerSubPix(gray, np.float32(centers), (5, 5), (-1, -1), criteria)
                
                frame_points[cam_id] = centers
            else:
                print(f"  [Frame {frame_idx}] Grid NOT found in Cam {cam_id}")
                frame_success = False
                break # If one camera fails to see the grid, the whole sync frame is dropped

        # If all 4 cameras successfully saw the 42 dots in this frame
        if frame_success:
            for cam_id in range(NUM_CAMERAS):
                points_2d[cam_id][frame_idx] = frame_points[cam_id]
            successful_sync_frames.append(frame_idx)
            print(f"  [Frame {frame_idx}] Success. Stored 42 points for all 4 cameras.")

    print(f"Phase 1 Complete! Found {len(successful_sync_frames)} fully synchronized frames.")
    return points_2d, successful_sync_frames

# ====================================================================
# Example Execution
# ====================================================================
if __name__ == "__main__":
    # Replace this with the actual path to your image directories
    # e.g., "C:/data/calibration_images/"
    BASE_DIRECTORY = "./data" 
    
    # Ensure you create dummy folders to test the script if you don't have images yet
    # os.makedirs(os.path.join(BASE_DIRECTORY, "cam0"), exist_ok=True)
    # etc...

    # Run the extraction
    # points_2d, valid_frames = extract_2d_grid_points(BASE_DIRECTORY, file_extension="png")
    
    # Later in Phase 2, we will use `points_2d` to extract Intrinsics and Extrinsics.
    pass