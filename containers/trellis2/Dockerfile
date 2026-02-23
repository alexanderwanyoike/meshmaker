# Trellis 2 RunPod Serverless Container
# Image-to-3D generation using Microsoft TRELLIS.2-4B

FROM runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04

ENV PYTHONUNBUFFERED=1
ENV HF_HOME=/runpod-volume/huggingface
ENV TRANSFORMERS_CACHE=/runpod-volume/huggingface
ENV OPENCV_IO_ENABLE_OPENEXR=1
ENV PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

# System dependencies
RUN apt-get update && apt-get install -y \
    git-lfs libjpeg-dev libgl1-mesa-glx libglib2.0-0 zlib1g-dev \
    && rm -rf /var/lib/apt/lists/* \
    && git lfs install

WORKDIR /app

# Upgrade PyTorch to 2.6.0 (required by Trellis 2)
# Must fully remove base image's 2.4.0 packages first — leftover .so files
# cause circular import errors in torchvision._meta_registrations
RUN pip uninstall -y torch torchvision torchaudio 2>/dev/null; \
    rm -rf /usr/local/lib/python3.11/dist-packages/torch* && \
    pip install --no-cache-dir \
    torch==2.6.0 torchvision==0.21.0 \
    --index-url https://download.pytorch.org/whl/cu124

# Clone Trellis 2 with submodules
RUN git clone -b main https://github.com/microsoft/TRELLIS.2.git --recursive /app/trellis2

WORKDIR /app/trellis2

# Install Python dependencies
RUN pip install --no-cache-dir \
    imageio imageio-ffmpeg tqdm easydict \
    opencv-python-headless ninja trimesh \
    transformers Pillow kornia timm \
    gradio==6.0.1 tensorboard pandas lpips zstandard

# Install utils3d
RUN pip install --no-cache-dir \
    git+https://github.com/EasternJournalist/utils3d.git@9a4eb15e4021b67b12c460c7057d642626897ec8

# Target GPU architectures for CUDA extension builds (no GPU available in CI)
# 8.0=A100, 8.6=A6000/RTX3090, 8.9=RTX4090/L40, 9.0=H100
ENV TORCH_CUDA_ARCH_LIST="8.0;8.6;8.9;9.0+PTX"

# Build CUDA extensions
# flash-attn MUST be rebuilt from source against PyTorch 2.6.0
# The base image ships flash-attn for 2.4.0 — force remove then rebuild
RUN pip uninstall -y flash-attn 2>/dev/null; \
    pip install --no-cache-dir --force-reinstall flash-attn --no-build-isolation

RUN git clone --depth 1 --branch v0.4.0 https://github.com/NVlabs/nvdiffrast.git /tmp/nvdiffrast && \
    pip install --no-cache-dir --no-build-isolation /tmp/nvdiffrast && rm -rf /tmp/nvdiffrast

RUN git clone --depth 1 --branch renderutils https://github.com/JeffreyXiang/nvdiffrec.git /tmp/nvdiffrec && \
    pip install --no-cache-dir --no-build-isolation /tmp/nvdiffrec && rm -rf /tmp/nvdiffrec

RUN git clone --depth 1 --recursive https://github.com/JeffreyXiang/CuMesh.git /tmp/cumesh && \
    pip install --no-cache-dir --no-build-isolation /tmp/cumesh && rm -rf /tmp/cumesh

RUN git clone --depth 1 --recursive https://github.com/JeffreyXiang/FlexGEMM.git /tmp/flexgemm && \
    pip install --no-cache-dir --no-build-isolation /tmp/flexgemm && rm -rf /tmp/flexgemm

RUN pip install --no-cache-dir --no-build-isolation /app/trellis2/o-voxel

# Trellis 2 is not a pip package — add to Python path
ENV PYTHONPATH="/app/trellis2:${PYTHONPATH}"

# Install RunPod SDK
RUN pip install --no-cache-dir runpod>=1.6.0 requests

COPY handler.py /app/handler.py
WORKDIR /app
CMD ["python", "-u", "handler.py"]
