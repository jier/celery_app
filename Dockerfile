# Use Python 3.11 as the base image
FROM python:3.11

# Set the working directory
WORKDIR /app

# TODO: Replace with uv-based install when containerizing.
# The project now uses uv + pyproject.toml; requirements.txt has been removed.
# COPY pyproject.toml uv.lock .
# RUN uv sync --frozen --no-dev


# Copy the rest of the application code to the container
COPY . .

# Set the command to run the Celery worker
CMD ["celery", "--app", "celery_app.celery", "worker","--pool", "eventlet", "--concurrency", "4", "--loglevel=info", "--events"]
