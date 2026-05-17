# =============================================================
# Dockerfile — Fraud Detection API
# Week 6: Model Deployment Preparation
# =============================================================
# 📌 What this does:
#   Packages your entire fraud detection API into a Docker
#   container so it can run on ANY computer or server.
#
# ▶️ How to build and run:
#   docker build -t fraud-detection-api .
#   docker run -p 8000:8000 fraud-detection-api
#
# ▶️ Then open: http://localhost:8000/docs
# =============================================================

# Start from an official Python image (slim = smaller size)
FROM python:3.12-slim

# Set working directory inside the container
WORKDIR /app

# Copy requirements file first (Docker caches this layer)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files into the container
COPY week5/models/ ./week5/models/
COPY week6/week6_api.py ./week6_api.py

# Create log directory
RUN mkdir -p week6/logs

# Expose port 8000 so it's accessible from outside the container
EXPOSE 8000

# Command to run when container starts
CMD ["python3", "week6_api.py"]
