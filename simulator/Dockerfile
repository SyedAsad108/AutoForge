FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy only the requirements file first to leverage Docker build cache
COPY simulator/requirements.txt /app/simulator/

# Install python dependencies
RUN pip install --no-cache-dir -r /app/simulator/requirements.txt

# Copy the entire workspace into the container
COPY . /app/

# Command to run the simulator
CMD ["python", "simulator/main.py"]
