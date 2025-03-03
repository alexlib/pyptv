# PyPTV Development Guide

## Build, Run & Test Commands
- Install: `pip install -e .`
- Build: `python -m build`
- Run GUI: `python -m pyptv.pyptv_gui`
- Run CLI: `python -m pyptv.cli`
- Run all tests: `pytest`
- Run specific test: `pytest tests/test_cli.py::test_cli_template -v`
- Run with test pattern: `pytest -k "cli"`
- Lint: `flake8 . --count --select=E9,F63,F7,F82 --ignore=F821 --show-source --statistics`

## Code Style Guidelines
- Formatting: Black with line length 88 (`black .`)
- Imports: Grouped by standard, third-party, then local imports
- Naming: snake_case for variables/functions, CamelCase for classes
- Type Annotations: Not currently used (consider adding for new code)
- Error Handling: Use try/except blocks for specific exceptions
- Comments: Document public functions with docstrings
- GUI Components: Follow traits/traitsui patterns
- Plugin Architecture: Follow existing plugin patterns when extending
- Version bumping: Use `python bump_version.py --patch` for incremental updates