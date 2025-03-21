#!/bin/bash

# Default OpenPTV wheel path - adjust Python version as needed
DEFAULT_WHEEL="../openptv/py_bind/dist/optv-0.3.0-cp311-cp311-linux_x86_64.whl"

# Setup development environment with the default wheel
./setup-dev-env.sh "$DEFAULT_WHEEL"