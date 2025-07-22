# ================================
# STAGE 1 – Scarico i modelli (CPU only)
# ================================
FROM python:3.8-slim AS model-downloader

RUN apt-get update && apt-get install -y git git-lfs && rm -rf /var/lib/apt/lists/*
RUN pip install --upgrade pip
RUN pip install torch==2.0.1+cpu transformers

# Scarica i modelli nella cache Hugging Face
RUN python -c "\
from transformers import AutoTokenizer, AutoModelForCausalLM; \
AutoTokenizer.from_pretrained('microsoft/Phi-3.5-mini-instruct'); \
AutoModelForCausalLM.from_pretrained('microsoft/Phi-3.5-mini-instruct', device_map='cpu')"

# ================================
# STAGE 2 – Runtime su Jetson (con CUDA)
# ================================
FROM nvcr.io/nvidia/l4t-base:r35.2.1

WORKDIR /app

# Dipendenze di sistema
RUN apt-get update && apt-get install -y \
    python3-pip python3-dev libjpeg-dev libpng-dev libglib2.0-0 libsm6 libxext6 libxrender-dev git git-lfs \
    && rm -rf /var/lib/apt/lists/*

# Installazione torch GPU
ENV TORCH_INSTALL=https://developer.download.nvidia.cn/compute/redist/jp/v511/pytorch/torch-2.0.0+nv23.05-cp38-cp38-linux_aarch64.whl

RUN python3 -m pip install --upgrade pip && \
    python3 -m pip install numpy==1.24.4 && \
    python3 -m pip install --no-cache-dir $TORCH_INSTALL

# Requisiti Python
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# Copia i modelli dalla fase precedente
COPY --from=model-downloader /root/.cache/huggingface /root/.cache/huggingface

# App
COPY shoppingassistantservice.py .

EXPOSE 8080
CMD ["python3", "shoppingassistantservice.py"]
