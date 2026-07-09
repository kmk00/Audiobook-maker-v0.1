FROM nvidia/cuda:12.8.0-cudnn-devel-ubuntu22.04

WORKDIR /app

RUN apt-get update && apt-get install -y \
    sox \
    libsox-fmt-all \
    git \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN ln -s /usr/bin/python3 /usr/bin/python

RUN pip install --no-cache-dir --pre torch \
    --index-url https://download.pytorch.org/whl/nightly/cu128 \
    && pip install --no-cache-dir --pre torchvision torchaudio --no-deps \
    --index-url https://download.pytorch.org/whl/nightly/cu128

COPY requirements_QWENTTS.txt .

RUN pip install --no-cache-dir numpy \
    && pip install --no-cache-dir -r requirements_QWENTTS.txt

COPY . /app/

CMD ["python", "qwen_worker.py"]