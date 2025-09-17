# Use Python 3.11 slim image
FROM python:3.11-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Working directory
WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .

# Upgrade pip and install dependencies
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend and data
COPY backend/ ./backend
COPY data/ ./data

# Expose port
EXPOSE 8000

# Start FastAPI app using gunicorn
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "backend.app:app", "--bind", "0.0.0.0:8000", "--workers", "1", "--log-level", "debug"]
