FROM rayproject/ray-ml:latest

WORKDIR /app

COPY ./serve ./serve/
COPY setup.py ./
COPY setup.cfg ./
COPY ./feature_store ./feature_store/

RUN pip install -e .

CMD ["python", "serve/main.py"]
