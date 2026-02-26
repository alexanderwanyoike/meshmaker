# Make It Animatable (MIA) RunPod Serverless Container
# Inference: GLB mesh -> FBX with Mixamo skeleton + skin weights
# pytorch3d 0.7.7 requires CUDA 12.1 (not 12.4)

FROM runpod/pytorch:2.1.2-py3.11-cuda12.1.1-devel-ubuntu22.04

ENV PYTHONUNBUFFERED=1
ENV HF_HOME=/runpod-volume/huggingface

# System deps for mesh loading (trimesh/open3d)
RUN apt-get update && apt-get install -y \
    git \
    git-lfs \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/* \
    && git lfs install

# Clone Make-It-Animatable
RUN git clone https://github.com/jasongzy/Make-It-Animatable.git /app/mia
WORKDIR /app/mia

# Install MIA dependencies
# pytorch3d 0.7.7 wheel built for pt2.1.2+cu121 from miropsota's builder
# bpy==4.3.0 for headless FBX export
RUN pip install --no-cache-dir \
    --extra-index-url https://download.pytorch.org/whl/cu121 \
    --extra-index-url https://miropsota.github.io/torch_packages_builder \
    pytorch3d==0.7.7+pt2.1.2cu121 \
    -r requirements.txt \
    bpy==4.3.0

RUN pip install --no-cache-dir runpod>=1.6.0 huggingface_hub

COPY handler.py /app/handler.py
WORKDIR /app
CMD ["python", "-u", "handler.py"]
