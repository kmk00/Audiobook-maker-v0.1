FROM nvidia/cuda:12.8.0-cudnn-devel-ubuntu22.04

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN ln -s /usr/bin/python3 /usr/bin/python

COPY requirements_whisper.txt .
RUN pip install --no-cache-dir -r requirements_whisper.txt

COPY . /app/

CMD ["python", "whisper_worker.py"]
