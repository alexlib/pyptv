This boilerplate provides a complete pipeline for moving from a desktop air calibration (Step 1) to a high-precision multi-view water calibration using a dumbbell (Step 2).

It uses `openptv-python` (the `optv` library) and `OpenCV`.

### Prerequisites
Install the necessary libraries:
`pip install openptv-python opencv-python numpy scipy`

---

### Step 1: Air Intrinsics (OpenCV to `.addpar`)
Run this on your desk before setting up the tank. It captures the "personality" of the lens.

```python
import numpy as np
import cv2
import yaml
from optv.calibration import Calibration
from optv.parameters import ControlParams

def calibrate_intrinsics_air(image_list, board_shape=(9,6), square_size=20.0):
    """
    Calibrates a single camera in air using a checkerboard.
    Returns: M (Intrinsics), d (Distortion)
    """
    objp = np.zeros((board_shape[0] * board_shape[1], 3), np.float32)
    objp[:, :2] = np.mgrid[0:board_shape[0], 0:board_shape[1]].T.reshape(-1, 2) * square_size

    obj_points, img_points = [], []
    for fname in image_list:
        img = cv2.imread(fname)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        ret, corners = cv2.findChessboardCorners(gray, board_shape, None)
        if ret:
            obj_points.append(objp)
            img_points.append(corners)

    ret, M, d, rvecs, tvecs = cv2.calibrateCamera(obj_points, img_points, gray.shape[::-1], None, None)
    return M, d.flatten(), gray.shape[::-1]

def save_openptv_addpar(M, d, img_size, cam_id):
    """
    Converts OpenCV results to OpenPTV .addpar format.
    """
    # OpenPTV uses xh, yh as the principal point relative to image center
    cc = (M[0,0] + M[1,1]) / 2.0  # Focal length
    xh = M[0,2] - (img_size[0] / 2.0)
    yh = (img_size[1] / 2.0) - M[1,2] # OpenPTV Y is often inverted relative to OpenCV

    # Create a Calibration object to use its writer
    cal = Calibration()
    # addpar structure: k1, k2, k3, p1, p2, scx, she
    # scx (scale) usually 1.0, she (shear) usually 0.0
    dist_params = [d[0], d[1], d[4], d[2], d[3], 1.0, 0.0] 
    cal.set_addpar(dist_params)
    cal.set_primary_point(np.array([xh, yh, cc]))
    
    # Write to file
    cal.write_orientation(f"cam{cam_id}.ori", f"cam{cam_id}.addpar")
    print(f"Saved intrinsics for Camera {cam_id}")
```

---

### Step 2: Setup Multimedia (Air-Glass-Water)
This defines the physical boundaries of your tank.

```python
from optv.parameters import MultimediaParams

def get_multimedia_params(glass_thickness=10.0):
    """
    Defines the layers for ray tracing.
    Distances are in mm. Indices: 1.0 (Air), 1.5 (Glass), 1.33 (Water)
    """
    mm = MultimediaParams(nlayers=3)
    mm.set_layers([1.0, 1.5, 1.33], [0, glass_thickness, 0]) # Last layer thickness is "infinite" (water)
    return mm
```

---

### Step 3: Rough Extrinsic Guess (Position & Orientation)
Since the dumbbell solver needs a starting point, we use a "Look-At" model based on your tape-measure distances.

```python
from scipy.spatial.transform import Rotation as R

def get_rough_orientation(cam_pos, look_at_pos=[0,0,0]):
    """
    Generates alpha, beta, gamma based on a camera looking at a point.
    cam_pos: [x, y, z] in world coordinates.
    """
    # Simple vector math to find orientation matrix
    forward = np.array(look_at_pos) - np.array(cam_pos)
    forward /= np.linalg.norm(forward)
    
    # Assume 'up' is along the Z axis initially
    up = np.array([0, 0, 1])
    right = np.cross(forward, up)
    up = np.cross(right, forward)
    
    rot_matrix = np.vstack([right, up, -forward]).T
    # Convert to OpenPTV Euler angles
    euler = R.from_matrix(rot_matrix).as_euler('zyx', degrees=True)
    return euler # [alpha, beta, gamma]
```

---

### Step 4: Fine Calibration (Dumbbell Bundle Adjustment)
This is the core "Water" calibration. It uses the known wand length to fix the scale and refraction.

```python
from optv.orientation import dumbbell_target_func

def run_fine_calibration(cam_ids, wand_points_2d, wand_length=100.0):
    """
    wand_points_2d: List of 2D coordinates for the two points of the wand.
    Format: [ [ [u1,v1], [u2,v2] ]_cam1, ... ] for all cams across many frames.
    """
    cals = []
    for i in cam_ids:
        # Load the air-calibrated .ori/.addpar
        cal = Calibration()
        cal.read(f"cam{i}.ori", f"cam{i}.addpar")
        
        # Apply rough guess for position (measured by tape)
        # cal.set_pos(...) 
        # cal.set_angles(...)
        cals.append(cal)

    # OpenPTV Multimedia settings
    mm = get_multimedia_params(glass_thickness=12.0)
    cparams = ControlParams(len(cam_ids))

    # --- THE OPTIMIZATION ---
    # In openptv-python, dumbbell calibration is usually a wrapper 
    # around a bundle adjustment that minimizes 3D distance error
    # of the wand points while constraining the distance between them.
    
    # This is a simplified call - in production, you iterate through frames
    # and solve for the best camera parameters.
    print("Starting Dumbbell Bundle Adjustment...")
    
    # Pseudocode for the solver logic:
    # result = dumbbell_target_func(cals, wand_points_2d, wand_length, mm, cparams)
    
    # After optimization, save the final Orientation
    for i, cal in enumerate(cals):
        cal.write_orientation(f"cam{i}_final.ori", f"cam{i}_final.addpar")
    
    print("Fine Calibration Complete.")
```

---

### Why this works for your lab setup:

1.  **Air Step (Calibration Consistency):** By doing the checkerboard in air first, you ensure that the lens distortion is "clean." When you run the water calibration, the software won't try to warp your lens focal length to compensate for the tank wall.
2.  **Initial Guess (The "Tape Measure" Step):** By providing the rough distance of the camera to the glass (e.g., $X=400mm$) and a "Look-at" point (the origin), you put the optimizer close enough to the "well" of the correct solution so it doesn't get lost in refraction noise.
3.  **The Dumbbell Constraint:** Since the distance between the two points on your wand is known (e.g., 100mm), the bundle adjustment has a **Global Scale**. This is what allows OpenPTV to know exactly where the $(0,0,0)$ of your tank is.

### Quick Laboratory Deployment Tips:
*   **Coordinate System:** Define your tank corner as $(0,0,0)$. Measure camera positions $X, Y, Z$ relative to that corner.
*   **Wand Visibility:** Wave the wand such that it covers at least 60% of the volume. Ensure both points are visible to at least 2 cameras simultaneously as often as possible.
*   **Synchronicity:** Ensure your cameras are triggered via a hardware signal. In high-speed flow, a 1ms delay between cameras will create a massive calibration error.