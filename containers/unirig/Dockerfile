# UniRig RunPod Serverless Container
# Inference only: GLB mesh -> FBX with predicted skeleton + skin weights
# Merge step (applying rig to original mesh) is done locally in Blender

FROM runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04

ENV PYTHONUNBUFFERED=1
ENV HF_HOME=/runpod-volume/huggingface
ENV TRANSFORMERS_CACHE=/runpod-volume/huggingface
# pyrender needs headless OpenGL for skin voxelization
ENV PYOPENGL_PLATFORM=osmesa

# Install system dependencies
# - git-lfs: for cloning repos with large files
# - libgl1-mesa-glx, libglib2.0-0: for mesh loading (open3d/trimesh)
# - libegl1-mesa-dev + libosmesa6-dev: headless OpenGL (EGL + OSMesa fallback)
# - X11 libs: required by bpy (used in data extraction for all stages)
RUN apt-get update && apt-get install -y \
    git-lfs \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libegl1-mesa-dev \
    libosmesa6-dev \
    libxrender1 \
    libsm6 \
    libxext6 \
    libxi6 \
    libxxf86vm1 \
    libxfixes3 \
    libxkbcommon0 \
    && rm -rf /var/lib/apt/lists/* \
    && git lfs install

# Clone UniRig repository
WORKDIR /app
RUN git clone https://github.com/VAST-AI-Research/UniRig.git /app/unirig

# Install UniRig requirements
# --ignore-installed is needed because the base image has distutils-installed
# packages (blinker) that pip can't uninstall cleanly. Pin torch to the base
# image version so pytorch_lightning/lightning don't upgrade it and break the
# ABI for pre-built torch_scatter/torch_cluster wheels.
WORKDIR /app/unirig
RUN pip install --no-cache-dir --ignore-installed -r requirements.txt \
    "torch==2.4.0+cu124" --extra-index-url https://download.pytorch.org/whl/cu124

# Install CUDA-specific packages for cu124
# - spconv-cu124: sparse convolutions for point cloud processing
# - torch_scatter, torch_cluster: geometric deep learning ops
# These wheels must match the base image's torch version exactly.
RUN pip install --no-cache-dir \
    spconv-cu124 \
    torch_scatter -f https://data.pyg.org/whl/torch-2.4.0+cu124.html \
    torch_cluster -f https://data.pyg.org/whl/torch-2.4.0+cu124.html \
    && python -c "import torch; assert torch.__version__.startswith('2.4.'), f'Expected torch 2.4.x, got {torch.__version__}'" \
    && python -c "import torch_cluster; print('torch_cluster OK')"

# Install flash attention (may fail on some GPUs, non-fatal)
RUN pip install --no-cache-dir flash_attn || echo "Warning: flash_attn installation failed, will use fallback attention"

# Install RunPod SDK
RUN pip install --no-cache-dir runpod>=1.6.0

# Copy our custom handler
COPY handler.py /app/handler.py

# Set working directory back to /app
WORKDIR /app

# Set the entrypoint for RunPod serverless
CMD ["python", "-u", "handler.py"]
