"""
RunPod Serverless Handler for Make It Animatable (MIA)

Inference: GLB mesh -> FBX with Mixamo skeleton + skin weights
Mirrors MIA's app.py inference pipeline with PCAE models.
"""

import os
import sys
import base64
import tempfile
import time

import runpod

MIA_DIR = "/app/mia"
VOLUME_PATH = os.environ.get("VOLUME_PATH", "/runpod-volume")
MODEL_DIR = os.path.join(VOLUME_PATH, "mia_models")
HF_REPO_ID = "jasongzy/Make-It-Animatable"

# Add MIA source to path so its modules are importable
sys.path.insert(0, MIA_DIR)

_models = None


def download_models():
    """Download MIA checkpoints from HuggingFace to network volume if missing."""
    from huggingface_hub import hf_hub_download

    ckpt_dir = os.path.join(MODEL_DIR, "output", "best", "new")
    os.makedirs(ckpt_dir, exist_ok=True)

    checkpoints = ["bw.pth", "bw_normal.pth", "joints.pth", "joints_coarse.pth", "pose.pth"]
    for ckpt in checkpoints:
        dest = os.path.join(ckpt_dir, ckpt)
        if not os.path.exists(dest):
            print(f"Downloading {ckpt}...")
            hf_hub_download(
                repo_id=HF_REPO_ID,
                filename=ckpt,
                local_dir=ckpt_dir,
                local_dir_use_symlinks=False,
            )

    print(f"All MIA checkpoints available at {ckpt_dir}")
    return ckpt_dir


def load_models():
    """Load all 5 MIA PCAE models to GPU."""
    global _models
    if _models is not None:
        return _models

    print("Loading MIA models...")
    import torch

    ckpt_dir = download_models()
    device = "cuda" if torch.cuda.is_available() else "cpu"

    # Import model factory from MIA source
    from src.models import get_bw_model, get_joints_model, get_pose_model

    def load_ckpt(path, loader_fn):
        print(f"  Loading {os.path.basename(path)}...")
        ckpt = torch.load(path, map_location=device)
        model = loader_fn(ckpt.get("cfg", {}))
        model.load_state_dict(ckpt.get("model_state_dict", ckpt))
        model.to(device)
        model.eval()
        return model

    _models = {
        "bw": load_ckpt(os.path.join(ckpt_dir, "bw.pth"), get_bw_model),
        "bw_normal": load_ckpt(os.path.join(ckpt_dir, "bw_normal.pth"), get_bw_model),
        "joints": load_ckpt(os.path.join(ckpt_dir, "joints.pth"), get_joints_model),
        "coarse": load_ckpt(os.path.join(ckpt_dir, "joints_coarse.pth"), get_joints_model),
        "pose": load_ckpt(os.path.join(ckpt_dir, "pose.pth"), get_pose_model),
        "device": device,
    }

    print(f"MIA models loaded on {device}")
    return _models


def run_inference(glb_path):
    """
    Run the full MIA inference pipeline on a GLB mesh.

    Pipeline (mirrors app.py):
      1. Load mesh → sample 32k point cloud
      2. Normalise point cloud
      3. model_coarse  → coarse joint positions
      4. model_bw + model_bw_normal → blend weights
      5. model_joints  → refined joint positions
      6. model_pose    → pose transforms
      7. bw_post_process → anatomical constraints + sparsification

    Returns:
        (mesh, joints_world, bw_final)
    """
    import torch
    import trimesh
    from src.utils import sample_mesh, get_normalize_transform, bw_post_process

    models = load_models()
    device = models["device"]

    # Load mesh — handle Scene (multi-mesh GLB) by concatenating
    print(f"Loading mesh: {glb_path}")
    scene = trimesh.load(glb_path)
    if isinstance(scene, trimesh.Scene):
        mesh = scene.dump(concatenate=True)
    else:
        mesh = scene

    # Sample point cloud with normals
    print("Sampling point cloud (32768 points)...")
    pc, pc_normals = sample_mesh(mesh, 32768)

    # Normalise to unit sphere
    transform = get_normalize_transform(mesh)
    pc_norm = (pc - transform["center"]) / transform["scale"]

    pc_t = torch.from_numpy(pc_norm).float().unsqueeze(0).to(device)
    pc_normals_t = torch.from_numpy(pc_normals).float().unsqueeze(0).to(device)

    print("Running PCAE inference...")
    with torch.no_grad():
        # Coarse joint estimation
        coarse_joints = models["coarse"](pc_t)

        # Blend weight prediction (geometry + normal streams)
        bw = models["bw"](pc_t, coarse_joints)
        bw_normal = models["bw_normal"](pc_t, pc_normals_t, coarse_joints)

        # Refined joint estimation
        joints = models["joints"](pc_t, coarse_joints)

        # Pose transforms
        models["pose"](pc_t, joints)

    # Post-process: anatomical constraints + sparsification
    bw_final = bw_post_process(bw.cpu().numpy()[0], bw_normal.cpu().numpy()[0])

    # Un-normalise joints back to mesh space
    joints_np = joints.cpu().numpy()[0]
    joints_world = joints_np * transform["scale"] + transform["center"]

    return mesh, joints_world, bw_final


def export_fbx(mesh, joints, bw, output_path):
    """Export rigged mesh as FBX with Mixamo bone names using bpy."""
    # MIA's vis_blender function creates a Blender scene with the armature
    # (mixamorig:* bone names) and exports as FBX
    from src.vis_blender import vis_blender
    vis_blender(mesh, joints, bw, output_path)


def handler(job: dict) -> dict:
    """RunPod serverless handler."""
    job_input = job.get("input", {})

    mesh_b64 = job_input.get("mesh")
    if not mesh_b64:
        return {"error": "Missing required field: mesh (base64 encoded GLB)"}

    try:
        start_time = time.time()

        # Decode input mesh
        with tempfile.NamedTemporaryFile(suffix=".glb", delete=False) as f:
            f.write(base64.b64decode(mesh_b64))
            glb_path = f.name

        output_path = tempfile.mktemp(suffix=".fbx")

        try:
            mesh, joints, bw = run_inference(glb_path)
            export_fbx(mesh, joints, bw, output_path)

            with open(output_path, "rb") as f:
                fbx_b64 = base64.b64encode(f.read()).decode("utf-8")

            processing_time = time.time() - start_time
            print(f"MIA inference complete in {processing_time:.2f}s, {len(joints)} bones")

            return {
                "output": fbx_b64,
                "format": "fbx",
                "processing_time": processing_time,
                "bone_count": len(joints),
            }

        finally:
            if os.path.exists(glb_path):
                os.unlink(glb_path)
            if os.path.exists(output_path):
                os.unlink(output_path)

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
    print("MIA models loaded successfully!")
except Exception as e:
    print(f"Warning: Model pre-loading failed: {e}")
    print("Models will be loaded on first request.")

# Start RunPod serverless
runpod.serverless.start({"handler": handler})
