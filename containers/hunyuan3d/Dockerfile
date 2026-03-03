# Hunyuan3D 2.1 RunPod Serverless Container
# Image/text-to-3D mesh generation using Tencent Hunyuan3D 2.1

FROM nvidia/cuda:12.4.1-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV HF_HOME=/runpod-volume/huggingface
ENV TRANSFORMERS_CACHE=/runpod-volume/huggingface
ENV PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

# System dependencies
RUN apt-get update && apt-get install -y \
    python3.11 python3.11-dev python3.11-venv python3-pip \
    git git-lfs curl wget \
    libjpeg-dev libpng-dev libgl1-mesa-glx libglib2.0-0 \
    zlib1g-dev ninja-build \
    && rm -rf /var/lib/apt/lists/* \
    && git lfs install

# Set python3.11 as default
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1 && \
    curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11

WORKDIR /app

# Install PyTorch 2.5.1+cu124
RUN pip install --no-cache-dir \
    torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 \
    --index-url https://download.pytorch.org/whl/cu124

# Clone Hunyuan3D 2.1
RUN git clone --depth 1 https://github.com/Tencent/Hunyuan3D-2.git /app/hunyuan3d

WORKDIR /app/hunyuan3d

# Install requirements
RUN pip install --no-cache-dir -r requirements.txt

# Target GPU architectures for CUDA extension builds (no GPU available in CI)
# 8.0=A100, 8.6=A6000/RTX3090, 8.9=RTX4090/L40, 9.0=H100
ENV TORCH_CUDA_ARCH_LIST="8.0;8.6;8.9;9.0+PTX"

# Build CUDA extensions: custom_rasterizer
RUN cd /app/hunyuan3d/hy3dgen/texgen/custom_rasterizer && \
    pip install --no-cache-dir --no-build-isolation .

# Build CUDA extensions: DifferentiableRenderer
RUN cd /app/hunyuan3d/hy3dgen/texgen/differentiable_renderer && \
    pip install --no-cache-dir --no-build-isolation .

# Hunyuan3D is not a pip package — add to Python path
ENV PYTHONPATH="/app/hunyuan3d:${PYTHONPATH}"

# Install RunPod SDK and utilities
RUN pip install --no-cache-dir runpod>=1.6.0 requests huggingface_hub

COPY handler.py /app/handler.py
WORKDIR /app
CMD ["python", "-u", "handler.py"]
