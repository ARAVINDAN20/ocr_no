# =============================================================================
# ANPR Live Dashboard - Docker Image
# Multi-platform support: Windows, macOS, Linux
# =============================================================================

# Use Python 3.10 slim image for smaller size and better compatibility
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set working directory
WORKDIR /app

# Install system dependencies for OpenCV, EasyOCR, and video processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    # OpenCV dependencies
    libgl1 \
    libglib2.0-0t64 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    # Video processing
    ffmpeg \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    # Build essentials for some Python packages
    gcc \
    g++ \
    # Git for cloning if needed
    git \
    # Clean up
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy the application code
COPY . .

# Create necessary directories
RUN mkdir -p templates static/css static/js models

# Expose the application port
EXPOSE 5001

# Set default command
CMD ["python", "speed_lane_dashboard.py"]

# =============================================================================
# BUILD INSTRUCTIONS:
# docker build -t anpr-dashboard .
#
# RUN INSTRUCTIONS:
# docker run -p 5001:5001 anpr-dashboard
#
# Then open http://localhost:5001 in your browser
# =============================================================================
