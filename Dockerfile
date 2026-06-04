# ============================================================
# AgriVision (AgrowWeed) — Backend Docker Image
# For deployment on Render.com
# ============================================================

FROM python:3.10-slim

# Install system dependencies for OpenCV and PyTorch
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (for Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
# Note: torch CPU-only version to save space on Render free tier
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY server.py .

# Copy model weights (models/best.pt)
COPY models/ models/

# Expose port — Render injects PORT env var (usually 10000)
EXPOSE 10000

# Start with gunicorn — reads PORT env var automatically
# --timeout 300: allow 5 min for YOLO model to load on first request
# --preload: load app before forking workers (loads YOLO once)
CMD gunicorn server:app \
    --bind 0.0.0.0:${PORT:-10000} \
    --workers 1 \
    --timeout 300 \
    --preload \
    --log-level info
