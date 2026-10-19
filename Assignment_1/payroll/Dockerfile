FROM python:3.14.8-slim

WORKDIR /app
COPY payroll/requirements.txt payroll/payrates.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# payrates is only installed if the wheel matches the pinned sha256
COPY wheels/ /wheels/
RUN pip install --no-cache-dir --no-deps --require-hashes -r payrates.txt

COPY payroll/app.py .

RUN useradd --system app
USER app

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
