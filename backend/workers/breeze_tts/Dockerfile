FROM nvidia/cuda:12.8.0-cudnn-devel-ubuntu22.04

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    python3 \
    python3-pip \
    sox \
    libsox-fmt-all \
    && rm -rf /var/lib/apt/lists/*

RUN ln -s /usr/bin/python3 /usr/bin/python

# Install nightly PyTorch with Blackwell (sm_120) support
RUN pip install --no-cache-dir --pre torch \
    --index-url https://download.pytorch.org/whl/nightly/cu128 \
    && pip install --no-cache-dir --pre torchaudio --no-deps \
    --index-url https://download.pytorch.org/whl/nightly/cu128

# Breeze TTS 2 inference code (breeze_infer + models packages)
# cloned from https://github.com/breezeblue-ai/breeze-tts (see breeze-tts-src/)
COPY breeze-tts-src /opt/breeze-tts
ENV PYTHONPATH=/opt/breeze-tts

COPY requirements_breeze.txt .

# numpy first: the 'sox' package (qwen-tts dependency) imports it during
# its setup.py metadata generation
RUN pip install --no-cache-dir numpy

# strip torch/torchaudio from requirements so pip doesn't clobber the
# nightly build with a stable one
RUN grep -v -E '^torch' requirements_breeze.txt | pip install --no-cache-dir -r /dev/stdin

COPY . /app/

CMD ["python", "breeze_worker.py"]
