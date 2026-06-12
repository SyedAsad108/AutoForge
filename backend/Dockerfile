FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy only the requirements file first to leverage Docker build cache
COPY backend/requirements.txt /app/backend/

# Install python dependencies
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy the entire workspace into the container
COPY . /app/

# Expose FastAPI port
EXPOSE 8000

# Command to run FastAPI app
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
