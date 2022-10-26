FROM python:3.8-slim-buster

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN python3 -m pip install --upgrade pip setuptools wheel

WORKDIR /app

COPY setup.py ./
COPY setup.cfg ./
COPY ./feature_store ./feature_store/

RUN pip install -e .
