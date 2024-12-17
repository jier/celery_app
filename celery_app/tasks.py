from celery_app.celery import app
import numpy as np

@app.task(name='addition', bind=True)
def addition(*args, **kwargs):
    num1 = np.random.randint(0, 11)
    num2 = np.random.randint(0, 11)
    result = num1 + num2
    print(f'Adding {num1} + {num2} = {result}')
    return result

@app.task(name='multiplication', bind=True)
def multiplication(*args, **kwargs):
    num1 = np.random.randint(1, 11)
    num2 = np.random.randint(1, 11)
    result = num1 * num2
    print(f'Multiplication {num1} x {num2} = {result}')
    return result

@app.task(name='division', bind=True)
def division(*args, **kwargs):
    num1 = np.random.randint(1, 11)
    num2 = np.random.randint(1, 11)
    result = num1 / num2
    print(f'Division {num1} / {num2} = {result}')
    return result

@app.task(name='call_addition', bind=True)
def call_addition(*args, **kwargs):
    addition.apply_async()

@app.task(name='call_multiplication', bind=True)
def call_multiplication(*args, **kwargs):
    multiplication.apply_async()

@app.task(name='call_division', bind=True)
def call_division(*args, **kwargs):
    division.apply_async()