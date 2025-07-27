# Slim Dockerfile for local testing of pyptv (mimics GitHub Actions)
FROM python:3.11-slim

# Install system dependencies for Qt, traitsui, and scientific stack
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libxkbcommon-x11-0 \
    libxcb-xinerama0 \
    git \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /workspace

# Copy repo
COPY . /workspace

# Install pip, wheel, and setuptools
RUN pip install --upgrade pip wheel setuptools

# Install pyptv and dependencies
RUN pip install .
RUN pip install -r requirements-dev.txt || true

# Optionally install test dependencies for Qt
RUN pip install PySide6 traits traitsui pytest

# Run all tests
CMD ["xvfb-run", "pytest", "-v", "-x", "--tb=short"]
