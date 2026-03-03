"""
RunPod Serverless Handler for Hunyuan3D-Part (P3-SAM)

Inference: GLB mesh -> part-segmented submeshes (GLB per part).
Uses P3-SAM from the Hunyuan3D-Part repository.
"""

import os
import sys
import base64
import tempfile
import time

import runpod

PART_DIR = "/app/hunyuan3d-part"
VOLUME_PATH = os.environ.get("VOLUME_PATH", "/runpod-volume")

sys.path.insert(0, PART_DIR)
os.chdir(PART_DIR)

_initialized = False
_model = None


def load_model():
    """Load P3-SAM segmentation model."""
    global _initialized, _model
    if _initialized:
        return

    import torch

    # P3-SAM model loading from the Hunyuan3D-Part repo
    sys.path.insert(0, os.path.join(PART_DIR, "P3-SAM"))

    from model import P3SAM

    from huggingface_hub import hf_hub_download

    ckpt_dir = os.path.join(VOLUME_PATH, "p3sam_models")
    os.makedirs(ckpt_dir, exist_ok=True)

    ckpt_path = os.path.join(ckpt_dir, "p3sam.pt")
    if not os.path.exists(ckpt_path):
        print("Downloading P3-SAM checkpoint...")
        hf_hub_download(
            repo_id="tencent/Hunyuan3D-Part",
            filename="p3sam.pt",
            local_dir=ckpt_dir,
            local_dir_use_symlinks=False,
        )

    print("Loading P3-SAM model...")
    _model = P3SAM()
    _model.load_state_dict(torch.load(ckpt_path, map_location="cuda"))
    _model = _model.cuda().eval()

    _initialized = True
    print("P3-SAM ready!")


def handler(job: dict) -> dict:
    """RunPod serverless handler."""
    job_input = job.get("input", {})

    mesh_b64 = job_input.get("mesh")
    if not mesh_b64:
        return {"error": "Missing required field: mesh (base64 encoded GLB)"}

    try:
        load_model()
        start_time = time.time()

        import trimesh
        import numpy as np

        # Write input GLB to temp file
        with tempfile.NamedTemporaryFile(suffix=".glb", delete=False, dir="/tmp") as f:
            f.write(base64.b64decode(mesh_b64))
            input_path = f.name

        try:
            # Load mesh
            mesh = trimesh.load(input_path, force="mesh")

            # Run P3-SAM segmentation
            from inference import segment_mesh

            labels = segment_mesh(_model, mesh)

            # Group faces by label and export each part
            unique_labels = np.unique(labels)
            parts = []

            for label_id in unique_labels:
                face_mask = labels == label_id
                if not face_mask.any():
                    continue

                # Extract submesh for this label
                submesh = mesh.submesh([face_mask], append=True)

                # Export submesh as GLB
                with tempfile.NamedTemporaryFile(suffix=".glb", delete=False, dir="/tmp") as tmp:
                    submesh.export(tmp.name, file_type="glb")
                    with open(tmp.name, "rb") as f:
                        part_b64 = base64.b64encode(f.read()).decode("utf-8")
                    os.unlink(tmp.name)

                parts.append({
                    "name": f"part_{int(label_id)}",
                    "mesh": part_b64,
                    "face_count": int(face_mask.sum()),
                })

            processing_time = time.time() - start_time
            print(f"Segmented into {len(parts)} parts in {processing_time:.2f}s")

            return {
                "parts": parts,
                "metadata": {
                    "num_parts": len(parts),
                    "processing_time": round(processing_time, 2),
                    "total_faces": len(mesh.faces),
                },
            }

        finally:
            if os.path.exists(input_path):
                os.unlink(input_path)

    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc(),
        }


# Initialize on cold start
print("Initializing P3-SAM handler...")
try:
    load_model()
    print("P3-SAM ready!")
except Exception as e:
    print(f"Warning: Model pre-loading failed: {e}")
    print("Model will be loaded on first request.")

runpod.serverless.start({"handler": handler})
