from celery_app import app


@app.task
def add(x: int, y: int) -> int:
    result = x + y
    print("add task result ", result)
    return result


@app.task
def multiply(x: int, y: int) -> int:
    result = x * y
    print("multiply task ", result)
    return result

# main.py
from tasks import add 

if __name__ == "__main__":
    result = add.delay(4, 5)
    print('Task result: ', result.get())