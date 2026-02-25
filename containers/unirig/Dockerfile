# UniRig RunPod Serverless Container
# Inference only: GLB mesh -> FBX with predicted skeleton + skin weights
# Merge step (applying rig to original mesh) is done locally in Blender

FROM runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04

ENV PYTHONUNBUFFERED=1
ENV HF_HOME=/runpod-volume/huggingface
ENV TRANSFORMERS_CACHE=/runpod-volume/huggingface

# Install system dependencies
# - git-lfs: for cloning repos with large files
# - libgl1-mesa-glx, libglib2.0-0: for mesh loading (open3d/trimesh)
RUN apt-get update && apt-get install -y \
    git-lfs \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/* \
    && git lfs install

# Clone UniRig repository
WORKDIR /app
RUN git clone https://github.com/VAST-AI-Research/UniRig.git /app/unirig

# Install UniRig requirements
WORKDIR /app/unirig
RUN pip install --no-cache-dir --ignore-installed -r requirements.txt

# Install CUDA-specific packages for cu124
# - spconv-cu124: sparse convolutions for point cloud processing
# - torch_scatter, torch_cluster: geometric deep learning ops
RUN pip install --no-cache-dir \
    spconv-cu124 \
    torch_scatter -f https://data.pyg.org/whl/torch-2.4.0+cu124.html \
    torch_cluster -f https://data.pyg.org/whl/torch-2.4.0+cu124.html

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
