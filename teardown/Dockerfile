FROM redisventures/gcp-feast:1.0.0

WORKDIR /app
COPY ./teardown ./teardown/

WORKDIR /app/teardown
RUN pip install -r requirements.txt

WORKDIR /app
CMD ./teardown/teardown.sh
