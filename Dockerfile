FROM python:3.9

ENV PYTHONUNBUFFERED 1

WORKDIR /app/

RUN python -m venv venv
# Enable venv
ENV PATH="/venv/bin:$PATH"

RUN pip install aiogram aiosqlite sqlalchemy

CMD ["python", "chat.py", ]