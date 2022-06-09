FROM python:3.10-alpine

RUN apk update && apk upgrade && \
    apk add --no-cache bash git openssh

WORKDIR /app
COPY requirements.txt .

RUN pip install -r requirements.txt


COPY . .
