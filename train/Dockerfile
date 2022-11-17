FROM redisventures/redis-feast-gcp:1.0.0
WORKDIR /app
COPY ./train ./train/

WORKDIR /app/train
RUN pip install -r requirements.txt

WORKDIR /app
CMD ["python", "train/main.py"]