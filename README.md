# Celery with Redis, RabbitMQ and Flower Setup

This project sets up a Celery application with Redis as the broker and backend, and Flower for monitoring. For local development. For Docker you should ***uncomment line 9 in celery.py and comment line 6**. The setup uses Docker and Docker Compose for containerization.

## Project Structure

```tree
celery_app
├── Dockerfile
├── celery_app
│   ├── __init__.py
│   ├── celery.py
│   └── tasks.py
├── docker-compose.yml
└── requirements.txt
```

## Files

- **Dockerfile**: Defines the Docker image for the Celery worker.
- **celery_app/celery.py**: Initializes the Celery application.
- **celery_app/tasks.py**: Defines the Celery tasks.
- **celery_app/__init__.py**: Ensures the Celery app is imported.
- **docker-compose.yml**: Defines the services for Docker Compose.
- **requirements.txt**: Lists the Python dependencies.

## Setup Instructions

### Prerequisites

- Docker
- Docker Compose
- Redis (link)[https://redis.io/docs/latest/operate/oss_and_stack/install/install-redis/]
- Redis Insight (optional) (link)[https://redis.io/insight/]

### Steps to Run the Application

0. **Clone the repository**:
   ```sh
   git clone <repository-url>
   cd <repository-directory>
   ```
#### Container  step

1. **Build the Docker images**:
   ```sh
   docker-compose build
   ```

2. **Start the services**:
   ```sh
   docker-compose up
   ```

#### Local Step

1. **Start celery in one terminalk**:
   ```sh
   celery -A celery_app.celery worker --pool eventlet -c 4 -l info 
   ```
2. **Start flower in another terminal**:
   ```sh
   celery -A celery_app.celery flower -l debug
   ```
3. **Start celery beat in another terminal**:
   ```sh
   celery -A celery_app.celery beat -l debug
   ```

### Services

- **redis**: Redis server for message brokering and result storage. For local case
- **rabbitMQ**: message Broker. For container Case and Redis Result storare.
- **flower**: Flower monitoring tool for Celery.
- **celery**: Celery worker.
- **celery_beat**: Celery Beat scheduler for periodic tasks.

### Accessing Flower

Flower can be accessed at `http://localhost:5555` to monitor the Celery tasks. This goes for local start up commands as docker commands.

## Task Definitions

### `celery_app/tasks.py`

- **addition**: Adds two random numbers between 0 and 10.
- **call_addition**: Calls the `addition` task every 10 seconds.
-  **mutlitplication**: Mutliply two random numbers between 1 and 11.
- **call_multiplication**: Calls the `multiplication` task every 10 seconds.
- **division**: Divides two random numbers between 1 and 11.
- **call_division**: Calls the `division` task every 10 seconds.

### Example Task

```python
@app.task(name='celery_app.addition', bind=True)
def addition(*args, **kwargs):
    num1 = np.random.randint(0, 11)
    num2 = np.random.randint(0, 11)
    result = num1 + num2
    print(f'Adding {num1} + {num2} = {result}')
    return result
```

### Example Beat Task

```python
@app.task(name='call_addition', bind=True)
def call_addition(*args, **kwargs):
    addition.apply_async()
```
>Note both task and beat tasks contains params arguments. Without them celery will result in an error complaining about the mismatch of function definitions done during the intitialisation of the app.
## Configuration

### `celery_app/celery.py`

- **Broker URL**: `redis://127.0.0.1:6379/0` ->Local use case
- **Backend URL**: `redis://127.0.0.1:6379/0` ->Local use case
- **Broker URL**: `amqp://rabbitmq` ->Container use case
- **Backend URL**: `redis://redis` ->Container use case
- **Beat Schedule**: Runs `call_addition`, `call_multiplication`,`call_division` task every 10 seconds.

### `docker-compose.yml`

- **Redis**: Exposes port `6379`.
- **RabbitMQ**: Exposes port `5672` for applications to connect and `15672` for management port
- **Flower**: Exposes port `5555`.
- **Celery Worker**: Runs the Celery worker.
- **Celery Beat**: Runs the Celery Beat scheduler.

## Notes

- Ensure Docker and Docker Compose are installed and running on your machine.
- Adjust the configurations as needed for your environment.

## License

This project is licensed under the MIT License.
```

This `README.md` file provides a comprehensive guide to setting up and running your Celery application with Redis and Flower. Let me know if you need any further assistance!