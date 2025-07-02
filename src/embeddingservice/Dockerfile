# Stage unico, basato su immagine NVIDIA L4T con supporto PyTorch
# Scegli l’immagine più leggera compatibile con Jetson Nano
FROM nvcr.io/nvidia/l4t-base:r32.7.1

# Cartella di lavoro
WORKDIR /app

# Installazione dipendenze di sistema
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      python3-pip python3-dev libjpeg-dev libpng-dev libglib2.0-0 libsm6 libxext6 libxrender1 && \
    rm -rf /var/lib/apt/lists/*

# Installa pip e numpy
RUN python3 -m pip install --upgrade pip && \
    python3 -m pip install numpy==1.24.4

# Installa PyTorch ottimizzato per Jetson
ENV TORCH_WHL="https://developer.download.nvidia.cn/compute/redist/jp/v511/pytorch/torch-2.0.0+nv23.05-cp38-cp38-linux_aarch64.whl"
RUN python3 -m pip install --no-cache-dir $TORCH_WHL

# Copia requirements e installa le librerie Python aggiuntive (es. transformers, sentence-transformers)
COPY requirements.txt .
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# Copia il servizio di embedding
COPY embedding_service.py .

# Porta su cui il servizio Python ascolterà le richieste gRPC via HTTP
EXPOSE 8000

# Avvia il servizio
ENV PYTHONUNBUFFERED=1
CMD ["python3", "embedding_service.py"]
