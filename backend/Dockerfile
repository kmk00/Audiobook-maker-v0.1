FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements_API.txt .

RUN pip install --no-cache-dir -r requirements_API.txt

COPY . /app/

CMD ["python", "main.py"]