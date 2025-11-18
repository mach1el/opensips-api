FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
  build-essential \
  libpq-dev \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Build-time default (can be overridden with --build-arg PORT=8080)
ARG PORT=3000
# Runtime default (can be overridden with -e PORT=8080)
ENV PORT=${PORT}

# Note: EXPOSE is documentation only; it’s fine to be dynamic with ARG here.
EXPOSE ${PORT}

# Use sh -c so $PORT expands at runtime
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
