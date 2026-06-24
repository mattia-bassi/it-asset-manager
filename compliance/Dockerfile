FROM python:3.12-slim

LABEL maintainer="Mattia Bassi"
LABEL description="IT Asset Manager - Compliance Test Container (ISO 27001 / GDPR)"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY compliance_test.py .

RUN mkdir -p /app/reports

CMD ["python", "compliance_test.py"]
