Open issues and triage for pyptv
================================

This file was generated automatically from code TODO/NotImplemented markers.

1. quiverplot: implement radial data_type
   - File: `pyptv/quiverplot.py`
   - Description: support radial quiver plotting where vectors are radial from a center.
   - Priority: low

2. legacy_parameters: implement missing legacy handlers or document removal
   - File: `pyptv/legacy_parameters.py`
   - Description: multiple NotImplementedError placeholders for legacy formats.
   - Priority: medium

3. ptv: existing targets not implemented
   - File: `pyptv/ptv.py`
   - Description: `raise NotImplementedError("Existing targets are not implemented")`
   - Priority: medium

4. GUI: many menu actions are TODO stubs
   - Files: `pyptv/pyptv_gui.py`, `pyptv/pyptv_gui_ttk.py`
   - Description: implement core flows: Open, Init, Highpass, Detection.
   - Priority: high (for user workflows)

5. Tests: flaky or TODO tests
   - Files: `tests/` multiple
   - Description: triage failing tests and convert noisy notebooks out of test path.
   - Priority: high

6. Plugin discovery duplicated
   - Files: `pyptv/ui/ptv_core/bridge.py`, `pyptv/ui/ptv_core.py`, `pyptv/parameter_manager.py`
   - Description: centralize plugin discovery into a single helper.
   - Priority: medium

7. Packaging: dependency cleanup (PySide6/Traits vs Tk)
   - File: `pyproject.toml`
   - Description: consider optional extras and avoid forcing heavy GUI deps for Tk path.
   - Priority: low

How to proceed
---------------
- Create individual GitHub issues from these items when ready.
- Prioritize tests and core Open/Init flows first.

Generated on: 2025-08-25
