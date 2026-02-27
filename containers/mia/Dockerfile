# Make It Animatable (MIA) RunPod Serverless Container
# Inference: GLB mesh -> FBX with Mixamo skeleton + skin weights

FROM runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04

ENV PYTHONUNBUFFERED=1
ENV HF_HOME=/runpod-volume/huggingface

# System deps for mesh loading (trimesh) + X11 libs required by bpy
RUN apt-get update && apt-get install -y \
    git \
    git-lfs \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libxrender1 \
    libsm6 \
    libxext6 \
    libxi6 \
    libxxf86vm1 \
    libxfixes3 \
    libxkbcommon0 \
    && rm -rf /var/lib/apt/lists/* \
    && git lfs install

# Clone our fork of Make-It-Animatable (has infer.py — clean inference without Gradio)
RUN git clone https://github.com/alexanderwanyoike/Make-It-Animatable.git /app/mia
WORKDIR /app/mia

# Install MIA dependencies
# requirements.txt pins pytorch3d==0.7.7+pt2.1.2cu121 which conflicts with
# our pt2.4.0 base — strip that line and install our wheel instead.
# bpy==4.3.0 for headless FBX export (cp311 only, requires py3.11)
RUN grep -v "^pytorch3d" requirements.txt > /tmp/requirements_no_p3d.txt && \
    pip install --no-cache-dir \
    --extra-index-url https://download.pytorch.org/whl/cu124 \
    --extra-index-url https://miropsota.github.io/torch_packages_builder \
    pytorch3d==0.7.7+pt2.4.0cu121 \
    -r /tmp/requirements_no_p3d.txt \
    bpy==4.3.0

RUN pip install --no-cache-dir runpod>=1.6.0 huggingface_hub

# Download Mixamo template skeleton from MIA's HF repo.
# dataset_mixamo.py requires data/Mixamo/bones.fbx at import time.
COPY get_bones_fbx.py /tmp/get_bones_fbx.py
RUN python /tmp/get_bones_fbx.py

# Generate bones_vroid.fbx (59-bone extended skeleton for dataset_mixamo_additional.py)
COPY create_vroid_fbx.py /tmp/create_vroid_fbx.py
RUN python /tmp/create_vroid_fbx.py

COPY handler.py /app/handler.py
WORKDIR /app
CMD ["python", "-u", "handler.py"]
