# Hunyuan3D 2.1 RunPod Serverless Container
# Image/text-to-3D mesh generation using Tencent Hunyuan3D 2.1

FROM runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04

ENV PYTHONUNBUFFERED=1
ENV HF_HOME=/runpod-volume/huggingface
ENV PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

# System dependencies for CUDA extension builds and mesh processing
RUN apt-get update && apt-get install -y \
    git-lfs \
    libjpeg-dev libpng-dev libgl1-mesa-glx libglib2.0-0 \
    ninja-build \
    && rm -rf /var/lib/apt/lists/* \
    && git lfs install

WORKDIR /app

# Clone Hunyuan3D 2.1
RUN git clone --depth 1 https://github.com/Tencent/Hunyuan3D-2.git /app/hunyuan3d

WORKDIR /app/hunyuan3d

# Install requirements (pin diffusers<0.33 for PyTorch 2.4 compat)
RUN pip install --no-cache-dir "diffusers<0.33" && \
    pip install --no-cache-dir -r requirements.txt

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
