FROM dockerhub.timeweb.cloud/library/python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y gcc libpq-dev && apt-get clean

COPY megano_backend/requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt


COPY diploma-frontend ./diploma-frontend
RUN pip install --no-cache-dir setuptools wheel \
    && cd diploma-frontend \
    && rm -rf dist *.egg-info \
    && python setup.py sdist \
    && pip install --no-cache-dir dist/*.tar.gz

COPY . .
WORKDIR /app/megano_backend

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]