FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    git curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/main.py backend/luffy_agent.py ./

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

