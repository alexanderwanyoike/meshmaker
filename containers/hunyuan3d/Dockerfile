# Hunyuan3D 2.1 RunPod Serverless Container
# Image/text-to-3D mesh generation using Tencent Hunyuan3D 2.1

FROM runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04

ENV PYTHONUNBUFFERED=1
ENV HF_HOME=/runpod-volume/huggingface
ENV HY3DGEN_MODELS=/runpod-volume/hy3dgen_models
ENV PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

# System dependencies
# - X11 libs required by bpy (headless Blender for OBJ-to-GLB conversion)
# - OpenGL libs for mesh rendering
# - Build tools for CUDA extensions
# Matches proven working set from MIA container + upstream Hunyuan3D docker
RUN apt-get update && apt-get install -y \
    git-lfs \
    ninja-build \
    cmake \
    libjpeg-dev libpng-dev \
    libgl1-mesa-glx libglib2.0-0 libegl1-mesa-dev \
    libxrender1 libsm6 libxext6 libxi6 libxxf86vm1 libxfixes3 libxkbcommon0 \
    libeigen3-dev libcgal-dev \
    && rm -rf /var/lib/apt/lists/* \
    && git lfs install

WORKDIR /app

# Clone the 2.1 repo
RUN git clone --depth 1 https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1.git /app/hunyuan3d

WORKDIR /app/hunyuan3d

# Install curated requirements
COPY requirements.txt /app/requirements_serverless.txt
RUN pip install --no-cache-dir --ignore-installed -r /app/requirements_serverless.txt

# Target GPU architectures for CUDA extension builds (no GPU available in CI)
# 8.0=A100, 8.6=A6000/RTX3090, 8.9=RTX4090/L40, 9.0=H100
ENV TORCH_CUDA_ARCH_LIST="8.0;8.6;8.9;9.0+PTX"

# Build CUDA extensions: custom_rasterizer
RUN cd /app/hunyuan3d/hy3dpaint/custom_rasterizer && \
    pip install --no-cache-dir --no-build-isolation .

# Build CUDA extensions: DifferentiableRenderer
RUN cd /app/hunyuan3d/hy3dpaint/DifferentiableRenderer && \
    bash compile_mesh_painter.sh

# Download RealESRGAN for texture upscaling
RUN wget -q https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth \
    -P /app/hunyuan3d/hy3dpaint/ckpt

# Install RunPod SDK
RUN pip install --no-cache-dir runpod>=1.6.0

COPY handler.py /app/handler.py
WORKDIR /app
CMD ["python", "-u", "handler.py"]
