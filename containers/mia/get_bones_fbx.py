"""
Download Standard Run.fbx from MIA's HuggingFace repo and place it at:
  - data/Mixamo/bones.fbx       (required by dataset_mixamo.py)
  - data/Mixamo/bones_vroid.fbx (required by dataset_mixamo_additional.py)

Both are needed at import time. ADDITIONAL_BONES=False in init_models()
so the vroid path is never used for inference, but the import still runs.
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
shutil.copy(src, "/app/mia/data/Mixamo/bones_vroid.fbx")
print("bones.fbx and bones_vroid.fbx ready")
