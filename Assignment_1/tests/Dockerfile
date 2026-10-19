FROM python:3.14.8-slim

WORKDIR /tests
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN useradd --system app
USER app

CMD ["pytest", "-p", "no:cacheprovider", "/tests"]
