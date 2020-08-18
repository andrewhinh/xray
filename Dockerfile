FROM python:3.8-slim-buster

RUN apt-get update && apt-get install -y git python3-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip3 install --upgrade -r requirements.txt

RUN pip3 install --upgrade --no-deps -r no_deps.txt

COPY app app/

RUN python3 app/server.py

EXPOSE 5000

CMD ["python", "app/server.py", "serve"]
