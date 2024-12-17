# Use Python 3.11 as the base image
FROM python:3.11

# Set the working directory
WORKDIR /app

# Copy the requirements to the container
COPY requirements.txt .

# Install the required Python packages
RUN pip install --no-cache-dir -r requirements.txt


# Copy the rest of the application code to the container
COPY . .

# Set the command to run the Celery worker
CMD ["celery", "--app", "celery_app.celery", "worker","--pool", "eventlet", "--concurrency", "4", "--loglevel=info", "--events"]
