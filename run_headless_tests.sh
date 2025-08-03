#!/bin/bash
# Run only headless (non-GUI) tests
cd "$(dirname "$0")"
pytest tests/ "$@"
