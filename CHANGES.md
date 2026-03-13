# Changelog

All notable changes to PyPTV are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.3] - 2026-03-13

### Added
- `ptv.clone_calibration` helper for calibration workflows
- Marimo-based UI additions for interactive workflows
- Tests covering writable output folder behavior

### Changed
- Widened `_ensure_target_output_writable` type annotations to accept `Sequence[str | os.PathLike]`
- Updated release helper scripts to report the current PyPTV version consistently

### Fixed
- Results directory test handling
- Skipped test behavior in the automated test suite
- Misleading version messages in Windows installation helpers

## [0.4.2] - 2026-03-01

### Added
- NumPy 2.0+ support with full compatibility for NumPy 2.x series
- `build_wheels.sh` script for building universal wheels
- Local wheel installation support in `wheels/` folder
- Installation scripts now support installing from pre-built wheels

### Changed
- **NumPy**: Updated from `==1.26.4` to `>=2.0.0,<2.7` (supports NumPy 2.x)
- **optv**: Updated from `>=0.3.0` to `>=0.3.2` (includes NumPy 2.0+ support)
- **chaco**: Updated from `>=5.1.0` to `>=6.1.0` (NumPy 2 compatible)
- **enable**: Updated from `>=5.3.0` to `>=6.1.0` (NumPy 2 compatible)
- Installation scripts (`install_pyptv.sh`, `install_pyptv.bat`) now install optv from local wheel first
- Test version checks updated to validate NumPy >=2.0.0

### Fixed
- Version checks in `tests/test_environment.py` now accept version range instead of exact version
- Version checks in `scripts/verify_environment.py` updated for NumPy 2.x compatibility

### Technical Details
- pyptv is now distributed as a universal wheel (`py3-none-any`) compatible with Python 3.10+
- optv 0.3.2 requires NumPy >=2.0.0 (handled by local wheel in `wheels/` folder)
- All GUI dependencies (traitsui 8.0.0, pyface 8.0.0, chaco 6.1.1, enable 6.1.0) verified compatible with NumPy 2.x

### Installation
```bash
# Using uv (recommended)
uv venv --python 3.11
source .venv/bin/activate
uv pip install wheels/optv-0.3.2-*.whl
uv pip install wheels/pyptv-0.4.2-py3-none-any.whl

# Or install in editable mode
uv pip install -e .
```

### Migration Notes
- **Minimum NumPy version**: 2.0.0 (NumPy 1.x no longer supported)
- **optv requirement**: 0.3.2+ with NumPy 2.0+ support
- Existing installations should update optv to 0.3.2 or later

---

## [0.4.1] - Previous Release

See git history for details of previous releases.
