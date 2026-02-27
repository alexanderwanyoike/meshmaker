"""
Download Standard Run.fbx from MIA's HuggingFace repo and use it as
data/Mixamo/bones.fbx — required by dataset_mixamo.py at import time.
bones_vroid.fbx is handled separately by create_vroid_fbx.py.
"""
import os
import shutil

from huggingface_hub import hf_hub_download

src = hf_hub_download(
    repo_id="jasongzy/Make-It-Animatable",
    filename="data/Standard Run.fbx",
    local_dir="/tmp/mia_data",
)

os.makedirs("/app/mia/data/Mixamo", exist_ok=True)
shutil.copy(src, "/app/mia/data/Mixamo/bones.fbx")
print("bones.fbx ready")
