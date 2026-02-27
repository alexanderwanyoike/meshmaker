"""
RunPod Serverless Handler for Make It Animatable (MIA)

Inference: GLB mesh -> FBX with Mixamo skeleton + skin weights.
Calls MIA's app.py pipeline functions directly.
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

# Must be set before importing MIA modules — init_models() relies on cwd
os.chdir(MIA_DIR)
sys.path.insert(0, MIA_DIR)

# Mock Gradio before any MIA import — app.py is a Gradio UI but we only
# need its inference functions. This prevents import errors and removes
# the heavyweight Gradio dependency from the inference path.
sys.path.insert(0, "/app")
from gradio_mock import install as _install_gradio_mock
_install_gradio_mock()

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

    # Checkpoints live at output/best/new/ inside the HF repo
    ckpt_dir = os.path.join(VOLUME_PATH, "mia_models", "output", "best", "new")
    os.makedirs(ckpt_dir, exist_ok=True)
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

    from app import init_models
    init_models()
    _initialized = True
    print("MIA models loaded!")


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

        from app import prepare_input, preprocess, infer, vis, vis_blender, finish, DB

        with tempfile.NamedTemporaryFile(suffix=".glb", delete=False, dir="/tmp") as f:
            f.write(base64.b64decode(mesh_b64))
            glb_path = f.name

        db = DB()
        try:
            print("Stage 1: prepare_input")
            prepare_input(glb_path, is_gs=False, opacity_threshold=0.0, db=db, export_temp=True)

            print("Stage 2: preprocess")
            preprocess(db)

            print("Stage 3: infer")
            infer(input_normal=False, db=db)

            print("Stage 4: vis")
            vis(bw_fix=True, bw_vis_bone="LeftArm", no_fingers=no_fingers, db=db)

            print("Stage 5: vis_blender (FBX export)")
            vis_blender(
                reset_to_rest=False,
                no_fingers=no_fingers,
                rest_pose_type=rest_pose_type,
                ignore_pose_parts=None,
                animation_file=None,
                retarget=True,
                inplace=True,
                db=db,
            )

            finish(db=None)

            if not db.anim_path or not os.path.exists(db.anim_path):
                return {"error": f"Pipeline finished but no FBX found at {db.anim_path}"}

            with open(db.anim_path, "rb") as f:
                fbx_b64 = base64.b64encode(f.read()).decode("utf-8")

            bone_count = int(db.joints.shape[0]) if db.joints is not None else 0
            processing_time = time.time() - start_time
            print(f"Done in {processing_time:.2f}s, {bone_count} bones -> {db.anim_path}")

            return {
                "output": fbx_b64,
                "format": "fbx",
                "processing_time": processing_time,
                "bone_count": bone_count,
            }

        finally:
            if os.path.exists(glb_path):
                os.unlink(glb_path)
            # Clean up MIA's temp output dir
            if db.output_dir and os.path.exists(db.output_dir):
                shutil.rmtree(db.output_dir, ignore_errors=True)

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
