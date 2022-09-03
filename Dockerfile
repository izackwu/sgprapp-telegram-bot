# syntax=docker/dockerfile:1

FROM python:3.10.6-slim-buster
WORKDIR /sgprapp-bot

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY sgprapp/*.py sgprapp/
COPY bot.py .

ENTRYPOINT [ "python3", "bot.py" ]
