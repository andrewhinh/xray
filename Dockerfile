FROM python:3.8-slim-buster

RUN apt-get update && apt-get install -y git python3-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip3 install aiohttp==3.6.2

RUN pip3 install fastai==1.0.61

RUN pip3 install --no-deps -r requirements.txt

COPY app app/

RUN python3 app/server.py

EXPOSE 5000

CMD ["python3", "app/server.py", "serve"]
