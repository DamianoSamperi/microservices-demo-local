FROM nvcr.io/nvidia/l4t-base:r36.2.0

WORKDIR /app

# Dipendenze di sistema
RUN apt-get update && apt-get install -y \
    python3-pip python3-dev libjpeg-dev libpng-dev libglib2.0-0 libsm6 libxext6 libxrender-dev  \
    && rm -rf /var/lib/apt/lists/*

# Installazione torch GPU
ENV TORCH_INSTALL=https://developer.download.nvidia.com/compute/redist/jp/v60/pytorch/torch-2.4.0a0+07cecf4168.nv24.05.14710581-cp310-cp310-linux_aarch64.whl
RUN python3 -m pip install --upgrade pip && \
    python3 -m pip install numpy==1.24.4 && \
    python3 -m pip install --no-cache-dir $TORCH_INSTALL

# Requisiti Python
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# App
COPY shoppingassistantservice.py .

EXPOSE 8080
CMD ["python3", "shoppingassistantservice.py"]
