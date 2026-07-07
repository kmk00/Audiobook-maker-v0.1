FROM nvidia/cuda:12.8.0-cudnn-devel-ubuntu22.04

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN ln -s /usr/bin/python3 /usr/bin/python

# Install nightly PyTorch with Blackwell (sm_120) support
RUN pip install --no-cache-dir --pre torch \
    --index-url https://download.pytorch.org/whl/nightly/cu128 \
    && pip install --no-cache-dir --pre torchvision torchaudio --no-deps \
    --index-url https://download.pytorch.org/whl/nightly/cu128

COPY requirements_Omnivoice.txt .

# strip torch/torchaudio/torchvision from requirements so pip doesn't
# clobber the nightly build with a stable one
RUN pip install --no-cache-dir -r requirements_Omnivoice.txt

COPY . /app/

CMD ["python", "omnivoice_worker.py"]