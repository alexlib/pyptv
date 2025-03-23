# PyPTV Development Guide

## Testing with Docker

The easiest way to test PyPTV without affecting your local environment is using Docker:

```bash
# Run all tests in Docker
./run_docker_tests.sh
```

### Docker Test Environment Details

The test environment is defined in `Dockerfile.test` and uses:
- Ubuntu latest
- Python 3.11
- Miniconda
- NumPy 1.26.4
- OpenPTV (optv) 0.3.0

### Debugging in Docker

To debug issues interactively:

```bash
# Build the test image
docker build -t pyptv-test -f Dockerfile.test .

# Run container interactively
docker run -it --rm pyptv-test bash

# Inside container, run tests:
./run_tests.sh

# Or run specific components:
python scripts/verify_environment.py
pytest -v -x tests/test_environment.py
```

## Local Development Setup

If you prefer local development:

1. Install EDM (Enthought Deployment Manager)
2. Create and activate environment:
```bash
edm install -y enable
edm install -y numpy==1.26.4
edm install -y matplotlib
edm shell
```

3. Install dependencies:
```bash
python -m pip install optv==0.3.0 tqdm flake8 pytest pyptv \
    --index-url https://pypi.fury.io/pyptv \
    --extra-index-url https://pypi.org/simple
```

## Development Workflow

1. Create feature branch:
```bash
git checkout -b feature/your-feature-name
```

2. Make changes and test:
```bash
# Run tests in Docker (recommended)
./run_docker_tests.sh

# Or run tests locally
pytest -v -x --tb=short
```

3. Lint code:
```bash
flake8 . --count --select=E9,F63,F7,F82 --ignore=F821 --show-source --statistics
```

4. Submit PR:
- Ensure all tests pass
- Update documentation if needed
- Follow code style guidelines

## Version Management

- Bump version: `python bump_version.py --patch`
- Build package: `python -m build`
- Install locally: `pip install dist/pyptv-{version}-py3-none-any.whl`

## Code Style Guidelines

- Use Black formatter (line length 88)
- Follow PEP 8 naming conventions
- Add docstrings for public functions
- Keep functions focused and small
- Write tests for new features

## Dependencies

Critical version requirements:
- Python >= 3.10
- NumPy == 1.26.4
- OpenPTV (optv) == 0.3.0
- See `pyproject.toml` for complete list

## Common Issues

1. EDM Installation Problems:
   - Verify EDM version (3.7.0 required)
   - Check system dependencies

2. Test Data Issues:
   - Ensure test_cavity repository is cloned
   - Verify parameter files are copied correctly

3. Version Conflicts:
   - Use `scripts/verify_environment.py` to check versions
   - Follow exact versions in `pyproject.toml`

## Getting Help

- Open an issue on GitHub
- Contact the mailing list: openptv@googlegroups.com
- Check existing documentation: http://openptv-python.readthedocs.io
