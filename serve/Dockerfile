FROM rayproject/ray-ml:latest

RUN python3 -m pip install --upgrade pip setuptools wheel

WORKDIR /app
COPY . ./

RUN pip install -e .

WORKDIR /app
CMD ["python", "serve/main.py"]