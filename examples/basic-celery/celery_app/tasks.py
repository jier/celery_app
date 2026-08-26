import numpy as np

from celery_app.celery import app


@app.task(name="addition")
def addition() -> int:
    first = int(np.random.randint(0, 11))
    second = int(np.random.randint(0, 11))
    result = first + second
    print(f"Adding {first} + {second} = {result}")
    return result


@app.task(name="multiplication")
def multiplication() -> int:
    first = int(np.random.randint(1, 11))
    second = int(np.random.randint(1, 11))
    result = first * second
    print(f"Multiplication {first} x {second} = {result}")
    return result


@app.task(name="division")
def division() -> float:
    first = int(np.random.randint(1, 11))
    second = int(np.random.randint(1, 11))
    result = first / second
    print(f"Division {first} / {second} = {result}")
    return result


@app.task(name="call_addition")
def call_addition() -> None:
    addition.delay()


@app.task(name="call_multiplication")
def call_multiplication() -> None:
    multiplication.delay()


@app.task(name="call_division")
def call_division() -> None:
    division.delay()
