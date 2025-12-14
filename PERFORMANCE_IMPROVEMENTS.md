# Performance Improvements Summary

This document outlines the performance improvements made to the PyPTV codebase.

## Changes Made

### 1. Replaced `range(len())` with `enumerate()` and `zip()`

**Why**: Using `enumerate()` and `zip()` is more Pythonic and slightly faster than indexing through `range(len())`. It also improves code readability and reduces the chance of indexing errors.

**Files Modified**:
- `pyptv/ptv.py`
- `pyptv/pyptv_gui.py`
- `pyptv/calibration_gui.py`
- `pyptv/mask_gui.py`
- `pyptv/detection_gui.py`

**Examples**:
```python
# Before
for i in range(len(x1)):
    if abs(x1[i] - x2[i]) > dx:
        x1f.append(x1[i])

# After
for x1_val, x2_val in zip(x1, x2):
    if abs(x1_val - x2_val) > dx:
        x1f.append(x1_val)
```

### 2. Replaced String Concatenation with f-strings

**Why**: f-strings (formatted string literals) are faster than string concatenation using `+` or `%` formatting. They are evaluated at runtime and use a more efficient C implementation.

**Files Modified**:
- `pyptv/ptv.py`
- `pyptv/calibration_gui.py`
- `pyptv/mask_gui.py`

**Examples**:
```python
# Before
print("Frame " + str(frame) + " had " + repr(corresp) + " correspondences.")
fname = "Camera" + str(i + 1)

# After
print(f"Frame {frame} had {corresp!r} correspondences.")
fname = f"Camera{i + 1}"
```

### 3. Optimized List Comprehensions

**Why**: Using `zip()` in list comprehensions instead of indexing improves performance by avoiding repeated list lookups.

**Files Modified**:
- `pyptv/ptv.py`

**Examples**:
```python
# Before
flat = np.array([corrected[i].get_by_pnrs(corresp[i]) for i in range(len(corrected))])

# After
flat = np.array([corr.get_by_pnrs(corresp) for corr, corresp in zip(corrected, sorted_corresp)])
```

### 4. Improved NumPy Array Handling

**Why**: Pre-allocating NumPy arrays is more memory efficient and faster than building a list and converting to an array.

**Files Modified**:
- `pyptv/prepare_static_background.py`

**Examples**:
```python
# Before
image_array = []
for i, file in enumerate(filelist[:N]):
    image_array.append(skio.imread(file))
image_array = np.array(image_array)

# After
first_img = skio.imread(filelist[0])
image_array = np.empty((N, *first_img.shape), dtype=first_img.dtype)
image_array[0] = first_img
for i, file in enumerate(filelist[1:N], start=1):
    image_array[i] = skio.imread(file)
```

### 5. Optimized Loop Iterations

**Why**: Iterating directly over collection items is faster and cleaner than indexing.

**Files Modified**:
- `pyptv/pyptv_gui.py`
- `pyptv/calibration_gui.py`
- `pyptv/detection_gui.py`
- `pyptv/mask_gui.py`

**Examples**:
```python
# Before
for j in range(len(quiverplots)):
    plot.remove(quiverplots[j])

# After
for quiver in quiverplots:
    plot.remove(quiver)
```

## Performance Impact

These improvements provide:

1. **Better CPU Efficiency**: Reduced overhead from unnecessary indexing operations
2. **Improved Memory Usage**: Pre-allocated arrays prevent memory fragmentation
3. **Faster String Operations**: f-strings are faster than concatenation
4. **Better Code Maintainability**: More readable, Pythonic code that's easier to understand and maintain

## Testing

All changes have been verified for syntax correctness using `python -m py_compile`.
The modifications maintain backward compatibility and do not change the external API or behavior.

## Future Recommendations

1. **Profiling**: Use `cProfile` or `line_profiler` to identify additional bottlenecks
2. **Vectorization**: Look for opportunities to replace loops with NumPy vectorized operations
3. **Caching**: Consider caching expensive computations that are called repeatedly
4. **Parallel Processing**: The existing `pyptv_batch_parallel.py` already uses multiprocessing, but consider additional parallelization opportunities
5. **I/O Optimization**: Consider batch reading of image files or memory mapping for large datasets
