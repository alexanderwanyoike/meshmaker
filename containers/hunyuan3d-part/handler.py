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

# P3-SAM's auto_mask.py does sys.path.append('..') which resolves relative to CWD,
# so CWD must be P3-SAM/demo/ for it to find P3-SAM/model.py
sys.path.insert(0, os.path.join(PART_DIR, "P3-SAM"))
sys.path.insert(0, os.path.join(PART_DIR, "P3-SAM", "demo"))
os.chdir(os.path.join(PART_DIR, "P3-SAM", "demo"))

_initialized = False
_auto_mask = None


def load_model():
    """Load P3-SAM segmentation model via AutoMask."""
    global _initialized, _auto_mask
    if _initialized:
        return

    from auto_mask import AutoMask

    print("Loading P3-SAM model (ckpt_path=None triggers HF auto-download)...")
    _auto_mask = AutoMask(ckpt_path=None)

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

            # Run P3-SAM segmentation via AutoMask.predict_aabb()
            # Returns: aabb, face_ids (np.ndarray of int labels per face), processed_mesh
            aabb, face_ids, processed_mesh = _auto_mask.predict_aabb(mesh)

            # Group faces by label and export each part
            unique_labels = np.unique(face_ids)
            parts = []

            for label_id in unique_labels:
                face_mask = face_ids == label_id
                if not face_mask.any():
                    continue

                # Extract submesh for this label (use processed_mesh, not original)
                submesh = processed_mesh.submesh([face_mask], append=True)

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
                    "total_faces": len(processed_mesh.faces),
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
