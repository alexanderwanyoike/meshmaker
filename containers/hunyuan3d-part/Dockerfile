# Hunyuan3D-Part (P3-SAM) RunPod Serverless Container
# Inference: GLB mesh -> part-segmented submeshes (GLB per part)

FROM runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04

ENV PYTHONUNBUFFERED=1
ENV HF_HOME=/runpod-volume/huggingface
ENV TORCH_CUDA_ARCH_LIST="8.0;8.6;8.9;9.0+PTX"

# System deps for mesh processing + git-lfs for model downloads
RUN apt-get update && apt-get install -y \
    git \
    git-lfs \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libxrender1 \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/* \
    && git lfs install

# Clone the Hunyuan3D-Part repo (contains both P3-SAM and XPart)
RUN git clone https://github.com/Tencent-Hunyuan/Hunyuan3D-Part.git /app/hunyuan3d-part
WORKDIR /app/hunyuan3d-part

# Install Sonata backbone (P3-SAM's feature extractor, from Facebook Research).
# model.py imports: from models import sonata  (via XPart/partgen/)
RUN pip install --no-cache-dir "sonata-model @ git+https://github.com/facebookresearch/sonata.git"

# Install P3-SAM Python dependencies
RUN pip install --no-cache-dir \
    trimesh \
    fpsample \
    numba \
    scikit-learn \
    safetensors \
    huggingface_hub \
    runpod>=1.6.0

# Build chamfer3D CUDA extension (required for mesh-to-point-cloud projection)
RUN cd /app/hunyuan3d-part/P3-SAM/utils/chamfer3D && \
    python setup.py install

COPY handler.py /app/handler.py
WORKDIR /app
CMD ["python", "-u", "handler.py"]
