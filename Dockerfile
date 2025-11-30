FROM public.ecr.aws/docker/library/python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN pip install newrelic

COPY . .
COPY newrelic.ini .

ENV NEW_RELIC_APP_NAME="Devops_blacklist"
ENV NEW_RELIC_LOG=stdout
ENV NEW_RELIC_DISTRIBUTED_TRACING_ENABLED=true
ENV NEW_RELIC_LICENSE_KEY=71dee41a38e79ed3813dc1d0d5303ab0FFFFNRAL
ENV NEW_RELIC_LOG_LEVEL=info

EXPOSE 5000

CMD ["newrelic-admin", "run-program", "gunicorn", "--bind", "0.0.0.0:5000", "main:app"]

