from celery import Celery


# Initialize Celery app
# Local
app = Celery('celery_app',broker='redis://127.0.0.1:6379/0', backend='redis://127.0.0.1:6379/0',include=['celery_app.tasks'])

# Container
# app = Celery('celery_app',broker='amqp://rabbitmq', backend='redis://redis',include=['celery_app.tasks'])

# Schedule the call_addition task to run every 10 seconds
app.conf.beat_schedule = {
    'add-every-10-seconds': {
        'task': 'call_addition',
        'schedule': 10.0,
    },
    'mutliply-every-10-seconds': {
        'task': 'call_multiplication',
        'schedule': 10.0,
    },
    'divide-every-10-seconds': {
        'task': 'call_division',
        'schedule': 10.0,
    },
}

app.conf.update(
    result_expires=3600,
    task_serializer='json',
    accept_content=['json'],  
    result_serializer='json',
    timezone='Europe/Amsterdam',
    enable_utc=True,
)
        


if __name__ == '__main__':
    print("""
        Simple Celery Application to get the feeling'.
        You get two mode, local and container. 
        Uncomment one of the lines to develop locally or run with the container
        url containing 127.0.0.1 points to the local redis service that you are running
""")
    app.start()