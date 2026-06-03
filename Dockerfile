# ============================================================
# AgriVision (AgrowWeed) — Backend Docker Image
# For deployment on Render.com
# ============================================================

FROM python:3.10-slim

# Install system dependencies for OpenCV and PyTorch
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
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
COPY .env .

# Copy model weights if present (models/best.pt or yolov8n.pt)
# The model file should be placed in models/ directory
COPY models/ models/

# Expose port (Render uses PORT env var)
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:${PORT:-5000}/health', timeout=5)" || exit 1

# Start server
CMD ["python", "server.py"]
