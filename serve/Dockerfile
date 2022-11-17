FROM redisventures/redis-feast-gcp:1.0.0

WORKDIR /app
COPY ./serve ./serve/

WORKDIR /app/serve
RUN pip install -r requirements.txt

WORKDIR /app
CMD ["python", "serve/main.py"]
