FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY celery_app ./celery_app

CMD ["celery", "--app", "celery_app.celery", "worker", "--pool", "eventlet", "--concurrency", "4", "--loglevel=info"]
