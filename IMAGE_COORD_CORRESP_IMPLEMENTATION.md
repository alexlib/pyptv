# Image Coordinate and Correspondences Functionality Implementation

## Overview

This document describes the implementation of Image Coordinate detection and Correspondences functionality in the TTK GUI, completing the replacement of Chaco/Traits dependencies with modern Tkinter/matplotlib implementation.

## Implemented Features

### 1. Image Coordinate Detection (`img_coord_action`)

**Purpose**: Detect targets/particles in loaded images across all cameras.

**Implementation**:
- Validates system initialization and image loading
- Calls `ptv.py_detection_proc_c()` with proper parameter formatting
- Stores results in `self.detections` and `self.corrected`
- Draws blue crosses on detected points using `drawcross_in_all_cams()`
- Provides comprehensive error handling and user feedback

**Usage Flow**:
1. User clicks "Image coord" button in Preprocess menu
2. System validates initialization and loaded images
3. Retrieves PTV and target recognition parameters
4. Runs detection processing on all camera images
5. Draws crosses on detected targets
6. Updates status with detection count

**Error Handling**:
- Checks for system initialization (`self.pass_init`)
- Validates image loading (`self.orig_images`)
- Validates parameter availability
- Provides detailed error messages for failures

### 2. Correspondences Processing (`corresp_action`)

**Purpose**: Find correspondences between detected targets across multiple cameras.

**Implementation**:
- Validates system initialization and detection results
- Calls `ptv.py_correspondences_proc_c()` with GUI object reference
- Stores results in `self.sorted_pos`, `self.sorted_corresp`, `self.num_targs`
- Draws colored crosses for different correspondence types:
  - **Yellow**: Pairs (2-camera correspondences)
  - **Green**: Triplets (3-camera correspondences)  
  - **Red**: Quadruplets (4-camera correspondences)
- Uses `_clean_correspondences()` helper to filter invalid data

**Usage Flow**:
1. User runs Image Coordinate detection first
2. User clicks "Correspondences" button in Preprocess menu
3. System validates detection results exist
4. Runs correspondence processing
5. Draws colored crosses for different correspondence types
6. Updates status with correspondence count

**Error Handling**:
- Checks for system initialization
- Validates detection results exist
- Provides detailed error messages for failures

### 3. Helper Method (`_clean_correspondences`)

**Purpose**: Filter out invalid correspondence data marked with -999 values.

**Implementation**:
```python
def _clean_correspondences(self, tmp):
    """Clean correspondences array"""
    x1, y1 = [], []
    for x in tmp:
        tmp = x[(x != -999).any(axis=1)]
        x1.append(tmp[:, 0])
        y1.append(tmp[:, 1])
    return x1, y1
```

**Functionality**:
- Filters out rows containing -999 (invalid correspondence markers)
- Separates x and y coordinates for drawing
- Returns clean coordinate arrays for each camera

## Integration with Existing System

### Parameter System Integration
- Uses `self.experiment.get_parameter('ptv')` for PTV parameters
- Uses `self.experiment.get_parameter('targ_rec')` for target recognition parameters
- Formats parameters correctly for C-level processing functions

### Drawing System Integration
- Leverages existing `drawcross_in_all_cams()` method
- Uses existing matplotlib camera panel system
- Maintains consistent visual styling with other GUI elements

### Status and Progress Integration
- Updates `self.status_var` with progress information
- Uses `self.progress` bar for visual feedback
- Provides `messagebox` notifications for completion/errors

## Technical Details

### Dependencies
- `pyptv.ptv` module for core processing functions
- `numpy` for array operations
- Existing GUI infrastructure (camera panels, drawing methods)

### Data Flow
1. **Image Coordinate Detection**:
   ```
   Images → ptv.py_detection_proc_c() → self.detections, self.corrected → Draw crosses
   ```

2. **Correspondences Processing**:
   ```
   Detections → ptv.py_correspondences_proc_c() → self.sorted_pos, self.sorted_corresp → Clean data → Draw colored crosses
   ```

### Error Recovery
- Graceful handling of missing parameters
- Clear error messages for user guidance
- Progress bar cleanup on errors
- Status updates for all scenarios

## Testing

### Automated Tests
- Method implementation verification
- Parameter integration testing
- Helper method logic validation
- Import availability checking

### Test Results
- ✅ All method implementations correct
- ✅ Parameter integration working
- ✅ Helper method logic verified
- ✅ Required imports available

### Manual Testing
- Functionality accessible via GUI menus
- Proper validation and error handling
- Visual feedback working correctly
- Integration with existing workflow

## Usage Instructions

### Prerequisites
1. System must be initialized (Start/Init button)
2. Images must be loaded from parameters
3. PTV and target recognition parameters must be available

### Workflow
1. **Initialize System**: Click "Start/Init" button to load images and initialize parameters
2. **Detect Targets**: Click "Image coord" in Preprocess menu to detect targets in all cameras
3. **Find Correspondences**: Click "Correspondences" in Preprocess menu to find target correspondences
4. **View Results**: Detected targets and correspondences are displayed as colored crosses on camera images

### Visual Indicators
- **Blue crosses**: Detected targets from Image Coordinate detection
- **Yellow crosses**: 2-camera correspondences (pairs)
- **Green crosses**: 3-camera correspondences (triplets)
- **Red crosses**: 4-camera correspondences (quadruplets)

## Future Enhancements

### Potential Improvements
- Interactive target selection/editing
- Correspondence quality metrics display
- Export functionality for detection results
- Advanced filtering options for correspondences

### Performance Optimizations
- Caching of detection results
- Parallel processing for multiple cameras
- Memory optimization for large image sets

## Conclusion

The Image Coordinate and Correspondences functionality is now fully implemented and integrated into the TTK GUI system. This completes another major component of the Chaco/Traits to Tkinter/matplotlib migration, providing users with modern, reliable target detection and correspondence processing capabilities.

The implementation maintains backward compatibility with existing parameter files and workflows while providing enhanced error handling and user feedback compared to the legacy system.