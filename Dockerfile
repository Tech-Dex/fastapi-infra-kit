FROM python:3.12.1-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./
RUN pip install --upgrade pip && \
    pip install --no-cache-dir uv && \
    uv pip compile pyproject.toml -o requirements.txt && \
    pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--proxy-headers", "--port", "8000"]

