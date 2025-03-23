#!/bin/bash

# Build the test container
docker build -t pyptv-test -f Dockerfile.test .

# Run tests
docker run --rm pyptv-test