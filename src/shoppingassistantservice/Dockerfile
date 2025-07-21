# Usa un'immagine Python base compatibile con Jetson (ARM64)
#FROM nvcr.io/nvidia/l4t-pytorch:r35.2.1-pth2.0-py3
FROM nvcr.io/nvidia/l4t-base:r35.2.1
WORKDIR /app

# Installa dipendenze di sistema e python3-pip
RUN apt-get update && apt-get install -y \
    python3-pip python3-dev libjpeg-dev libpng-dev libglib2.0-0 libsm6 libxext6 libxrender-dev git git-lfs\
    && rm -rf /var/lib/apt/lists/* 

ENV TORCH_INSTALL=https://developer.download.nvidia.cn/compute/redist/jp/v511/pytorch/torch-2.0.0+nv23.05-cp38-cp38-linux_aarch64.whl
# Aggiorna pip, installa numpy 1.24.4 e poi installa il file wheel di Torch senza cache
RUN python3 -m pip install --upgrade pip && \
    python3 -m pip install numpy==1.24.4 && \
    python3 -m pip install --no-cache-dir $TORCH_INSTALL && \
    pip3 install gdown
COPY requirements.txt .
RUN pip3 install -r requirements.txt

ENV PYTHONUNBUFFERED=1

RUN git lfs install && \
    git clone https://huggingface.co/microsoft/Phi-3.5-mini-instruct /root/.cache/huggingface/my_local_model && \
    cd /root/.cache/huggingface/my_local_model && \
    git lfs pull


# Copia i file dell'app
COPY shoppingassistantservice.py .

# Espone la porta su cui gira Flask
EXPOSE 8080

# Avvia il servizio Flask
CMD ["python3", "shoppingassistantservice.py"]
