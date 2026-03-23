# Use Python 3.9.5 slim base image
FROM python:3.9.5-slim

# Set working directory inside backend
WORKDIR /app

# Install system dependencies needed for Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    libffi-dev \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt from backend folder
COPY backend/requirements.txt .

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend /app

# Expose port for Railpack / Heroku
ENV PORT=8000

# Start the backend app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
