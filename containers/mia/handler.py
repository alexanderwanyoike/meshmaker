"""
RunPod Serverless Handler for Make It Animatable (MIA)

Inference: GLB mesh -> FBX with Mixamo skeleton + skin weights.
Uses infer.py from our fork — clean interface with no Gradio dependency.
"""

import os
import sys
import shutil
import base64
import tempfile
import time

import runpod

MIA_DIR = "/app/mia"
VOLUME_PATH = os.environ.get("VOLUME_PATH", "/runpod-volume")
HF_REPO_ID = "jasongzy/Make-It-Animatable"

# Add MIA to path and set cwd — init_models() uses relative paths
sys.path.insert(0, MIA_DIR)
os.chdir(MIA_DIR)

_initialized = False


def setup_model_symlink():
    """Symlink /app/mia/output -> network volume so checkpoints persist."""
    volume_output = os.path.join(VOLUME_PATH, "mia_models", "output")
    os.makedirs(os.path.join(volume_output, "best", "new"), exist_ok=True)

    mia_output = os.path.join(MIA_DIR, "output")
    if os.path.exists(mia_output) and not os.path.islink(mia_output):
        shutil.rmtree(mia_output)
    if not os.path.exists(mia_output):
        os.symlink(volume_output, mia_output)
        print(f"Symlinked {mia_output} -> {volume_output}")


def download_models():
    """Download MIA checkpoints from HuggingFace to network volume if missing."""
    from huggingface_hub import hf_hub_download

    ckpt_dir = os.path.join(VOLUME_PATH, "mia_models", "output", "best", "new")
    checkpoints = ["bw.pth", "bw_normal.pth", "joints.pth", "joints_coarse.pth", "pose.pth"]
    for ckpt in checkpoints:
        dest = os.path.join(ckpt_dir, ckpt)
        if not os.path.exists(dest):
            hf_path = f"output/best/new/{ckpt}"
            print(f"Downloading {hf_path}...")
            hf_hub_download(
                repo_id=HF_REPO_ID,
                filename=hf_path,
                local_dir=os.path.join(VOLUME_PATH, "mia_models"),
                local_dir_use_symlinks=False,
            )
    print("All MIA checkpoints ready.")


def load_models():
    global _initialized
    if _initialized:
        return

    setup_model_symlink()
    download_models()

    from infer import init_models
    init_models()
    _initialized = True
    print("MIA ready!")


def handler(job: dict) -> dict:
    """RunPod serverless handler."""
    job_input = job.get("input", {})

    mesh_b64 = job_input.get("mesh")
    if not mesh_b64:
        return {"error": "Missing required field: mesh (base64 encoded GLB)"}

    no_fingers = job_input.get("no_fingers", False)
    rest_pose_type = job_input.get("rest_pose", None)

    try:
        load_models()
        start_time = time.time()

        from infer import run, DB

        with tempfile.NamedTemporaryFile(suffix=".glb", delete=False, dir="/tmp") as f:
            f.write(base64.b64decode(mesh_b64))
            glb_path = f.name

        try:
            fbx_path = run(glb_path, no_fingers=no_fingers, rest_pose_type=rest_pose_type)

            with open(fbx_path, "rb") as f:
                fbx_b64 = base64.b64encode(f.read()).decode("utf-8")

            processing_time = time.time() - start_time
            print(f"Done in {processing_time:.2f}s -> {fbx_path}")

            return {
                "output": fbx_b64,
                "format": "fbx",
                "processing_time": processing_time,
            }

        finally:
            if os.path.exists(glb_path):
                os.unlink(glb_path)

    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc(),
        }


# Initialize on cold start
print("Initializing MIA handler...")
try:
    load_models()
    print("MIA ready!")
except Exception as e:
    print(f"Warning: Model pre-loading failed: {e}")
    print("Models will be loaded on first request.")

runpod.serverless.start({"handler": handler})
