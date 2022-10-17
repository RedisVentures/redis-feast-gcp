FROM python:3.8-slim-buster

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN python3 -m pip install --upgrade pip setuptools wheel

WORKDIR /app
COPY . ./

RUN pip install -e .

WORKDIR /app/train
RUN pip install -r requirements.txt

RUN env

WORKDIR /app
CMD ["python", "train/main.py"]