FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

RUN groupadd --system app && useradd --system --gid app app

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

USER app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
