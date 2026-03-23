# Use official Python 3.9.5 image
FROM python:3.9.5-slim

# Set working directory
WORKDIR /app

# Copy backend requirements
COPY backend/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend /app

# Expose the port
EXPOSE 8000

# Start the app with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
