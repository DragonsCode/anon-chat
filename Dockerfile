FROM python:3.9

WORKDIR /app/

COPY . /app/

RUN python -m venv venv
# Enable venv
ENV PATH="/venv/bin:$PATH"

RUN pip install -r requirements.txt

CMD ["python", "chat.py"]