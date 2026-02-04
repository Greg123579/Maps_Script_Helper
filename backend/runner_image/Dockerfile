# Execution sandbox image
FROM python:3.11-slim

# Create working dirs
RUN mkdir -p /work /input /output /code
WORKDIR /work

# Set matplotlib config directory environment variable early
# This ensures matplotlib uses /output/.matplotlib (which will be mounted)
ENV MPLCONFIGDIR=/output/.matplotlib

# Install system dependencies for OpenCV and image processing
# libgl1 provides libGL.so.1 needed by OpenCV (replaces libgl1-mesa-glx in newer Debian)
# libglib2.0-0 is needed for some image processing libraries
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install known-good packages
COPY requirements.txt /work/requirements.txt
RUN pip install --no-cache-dir -r /work/requirements.txt

# Add the job runner and MapsBridge shim
COPY job_runner.py /work/job_runner.py
COPY MapsBridge.py /work/MapsBridge.py

# Make MapsBridge available as a module (add to Python path)
ENV PYTHONPATH="/work"

ENTRYPOINT ["python", "-u", "/work/job_runner.py"]
