#!/bin/bash
# Run all tests (headless and GUI) locally
cd "$(dirname "$0")"
pytest tests/ "$@"
pytest tests_gui/ "$@"
