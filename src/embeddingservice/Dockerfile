# Stage unico, basato su immagine NVIDIA L4T con supporto PyTorch
# Scegli l’immagine più leggera compatibile con Jetson Nano
#FROM nvcr.io/nvidia/l4t-base:r32.7.1
FROM nvcr.io/nvidia/l4t-pytorch:r32.7.1-pth1.10-py3
# Cartella di lavoro
WORKDIR /app
RUN sed -i '/kitware.com/d' /etc/apt/sources.list
# Installazione dipendenze di sistema
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      python3-pip python3-dev libjpeg-dev libpng-dev libglib2.0-0 libsm6 libxext6 libxrender1 || true && \
    rm -rf /var/lib/apt/lists/*

# Installa pip e numpy
RUN python3 -m pip install --upgrade pip && \
    python3 -m pip install numpy

# Installa PyTorch ottimizzato per Jetson
#ENV TORCH_WHL="https://developer.download.nvidia.cn/compute/redist/jp/v511/pytorch/torch-2.0.0+nv23.05-cp38-cp38-linux_aarch64.whl"
#RUN python3 -m pip install --no-cache-dir $TORCH_WHL
# Install python packages
RUN pip3 install --no-cache-dir future \
    && pip3 install --no-cache-dir --upgrade wheel mock pillow \
    && pip3 install --no-cache-dir testresources \
    && pip3 install --no-cache-dir setuptools==58.3.0 \
    && pip3 install --no-cache-dir Cython 
#    && pip3 install --no-cache-dir gdown

# Download the PyTorch wheel using gdown
#RUN gdown https://drive.google.com/uc?id=1TqC6_2cwqiYacjoLhLgrZoap6-sVL2sd -O torch-1.10.0a0+git36449ea-cp36-cp36m-linux_aarch64.whl

# Install the PyTorch wheel
#RUN pip3 install --no-cache-dir torch-1.10.0a0+git36449ea-cp36-cp36m-linux_aarch64.whl

# Clean up wheel file to reduce image size
#RUN rm torch-1.10.0a0+git36449ea-cp36-cp36m-linux_aarch64.whl

# Copia requirements e installa le librerie Python aggiuntive (es. transformers, sentence-transformers)
COPY requirements.txt .
RUN python3 -m pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y ca-certificates && update-ca-certificates
RUN pip3 install --upgrade certifi

# Copia il servizio di embedding
COPY embedding_service.py .

# Porta su cui il servizio Python ascolterà le richieste gRPC via HTTP
EXPOSE 8000

# Avvia il servizio
ENV PYTHONUNBUFFERED=1
CMD ["python3", "embedding_service.py"]
