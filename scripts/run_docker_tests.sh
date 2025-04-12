#!/bin/bash

# Clean up any existing containers/images and run tests in one line
docker stop $(docker ps -a | grep pyptv-test | awk '{print $1}') 2>/dev/null; docker rm $(docker ps -a | grep pyptv-test | awk '{print $1}') 2>/dev/null; docker rmi pyptv-test 2>/dev/null; docker image prune -f && docker build --no-cache -t pyptv-test -f Dockerfile.test . && docker run --rm pyptv-test
