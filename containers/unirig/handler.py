"""
RunPod Serverless Handler for UniRig

Automatic rigging: GLB mesh -> FBX with Mixamo-compatible skeleton

UniRig pipeline:
1. generate_skeleton.sh - Predict skeleton joints from mesh
2. generate_skin.sh - Predict skin weights
3. merge.sh - Combine skeleton + weights with original mesh -> FBX output
"""

import os
import sys
import base64
import tempfile
import time
import subprocess
import shutil
from pathlib import Path

import runpod

# Configuration
UNIRIG_DIR = "/app/unirig"
VOLUME_PATH = os.environ.get("VOLUME_PATH", "/runpod-volume")
EXPERIMENTS_DIR = os.path.join(UNIRIG_DIR, "experiments")

# HuggingFace model info
HF_REPO_ID = "VAST-AI/UniRig"
MODEL_SIZE_GB = 11.5  # Approximate total size


def setup_model_symlinks():
    """Create symlinks from experiments/ to network volume where models are stored."""
    volume_experiments = os.path.join(VOLUME_PATH, "unirig", "experiments")

    # Create volume experiments dir if needed
    os.makedirs(volume_experiments, exist_ok=True)

    # Remove existing experiments dir if it's not a symlink
    if os.path.exists(EXPERIMENTS_DIR) and not os.path.islink(EXPERIMENTS_DIR):
        shutil.rmtree(EXPERIMENTS_DIR)

    # Create symlink
    if not os.path.exists(EXPERIMENTS_DIR):
        os.symlink(volume_experiments, EXPERIMENTS_DIR)
        print(f"Created symlink: {EXPERIMENTS_DIR} -> {volume_experiments}")


def download_unirig_models():
    """Download UniRig models from HuggingFace to network volume if not present."""
    from huggingface_hub import snapshot_download

    volume_experiments = os.path.join(VOLUME_PATH, "unirig", "experiments")

    # Check for skeleton model (primary indicator models are downloaded)
    skeleton_marker = os.path.join(volume_experiments, "skeleton", "ckpt")
    skin_marker = os.path.join(volume_experiments, "skin", "ckpt")

    if os.path.exists(skeleton_marker) and os.path.exists(skin_marker):
        print(f"UniRig models already exist at {volume_experiments}")
        return

    print(f"Downloading UniRig models from {HF_REPO_ID} (~{MODEL_SIZE_GB}GB)...")

    # Download skeleton checkpoint
    print("Downloading skeleton checkpoint...")
    snapshot_download(
        repo_id=HF_REPO_ID,
        local_dir=volume_experiments,
        local_dir_use_symlinks=False,
        allow_patterns=["skeleton/**"],
    )

    # Download skin checkpoint
    print("Downloading skin checkpoint...")
    snapshot_download(
        repo_id=HF_REPO_ID,
        local_dir=volume_experiments,
        local_dir_use_symlinks=False,
        allow_patterns=["skin/**"],
    )

    print("UniRig models downloaded successfully!")


def load_models():
    """Initialize UniRig by setting up symlinks and downloading models."""
    print("Initializing UniRig...")
    setup_model_symlinks()
    download_unirig_models()
    print("UniRig initialization complete!")


def run_unirig_pipeline(input_glb_path: str, output_fbx_path: str, seed: int = 12345) -> dict:
    """
    Run the full UniRig pipeline: skeleton generation -> skin weights -> merge to FBX.

    Args:
        input_glb_path: Path to input GLB mesh file
        output_fbx_path: Path for output FBX file
        seed: Random seed for reproducibility

    Returns:
        Dictionary with timing info and status
    """
    timings = {}
    os.chdir(UNIRIG_DIR)

    # Create temp directory for intermediate files
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)

        # Copy input to temp dir with expected name
        input_mesh = temp_dir / "input.glb"
        shutil.copy(input_glb_path, input_mesh)

        # Intermediate output paths
        skeleton_output = temp_dir / "skeleton.fbx"
        skinned_output = temp_dir / "skinned.fbx"

        # Stage 1: Generate skeleton
        print("Stage 1: Generating skeleton...")
        start_time = time.time()

        skeleton_cmd = [
            "bash", "generate_skeleton.sh",
            str(input_mesh),
            str(skeleton_output),
            "--seed", str(seed),
        ]

        result = subprocess.run(
            skeleton_cmd,
            capture_output=True,
            text=True,
            cwd=UNIRIG_DIR,
        )

        if result.returncode != 0:
            raise RuntimeError(f"Skeleton generation failed: {result.stderr}")

        timings["skeleton_generation"] = time.time() - start_time
        print(f"  Skeleton generated in {timings['skeleton_generation']:.2f}s")

        # Stage 2: Generate skin weights
        print("Stage 2: Generating skin weights...")
        start_time = time.time()

        skin_cmd = [
            "bash", "generate_skin.sh",
            str(input_mesh),
            str(skeleton_output),
            str(skinned_output),
            "--seed", str(seed),
        ]

        result = subprocess.run(
            skin_cmd,
            capture_output=True,
            text=True,
            cwd=UNIRIG_DIR,
        )

        if result.returncode != 0:
            raise RuntimeError(f"Skin weight generation failed: {result.stderr}")

        timings["skin_generation"] = time.time() - start_time
        print(f"  Skin weights generated in {timings['skin_generation']:.2f}s")

        # Stage 3: Merge with original mesh
        print("Stage 3: Merging to final FBX...")
        start_time = time.time()

        merge_cmd = [
            "bash", "merge.sh",
            str(input_mesh),
            str(skinned_output),
            str(output_fbx_path),
        ]

        result = subprocess.run(
            merge_cmd,
            capture_output=True,
            text=True,
            cwd=UNIRIG_DIR,
        )

        if result.returncode != 0:
            raise RuntimeError(f"Merge failed: {result.stderr}")

        timings["merge"] = time.time() - start_time
        print(f"  Merged in {timings['merge']:.2f}s")

    return timings


def handler(job: dict) -> dict:
    """RunPod serverless handler."""
    job_input = job.get("input", {})

    # Get input mesh (base64 encoded GLB)
    mesh_b64 = job_input.get("mesh")
    if not mesh_b64:
        return {"error": "Missing required field: mesh (base64 encoded GLB)"}

    # Optional parameters
    output_format = job_input.get("format", "fbx").lower()
    seed = job_input.get("seed", 12345)

    if output_format != "fbx":
        return {"error": f"Unsupported output format: {output_format}. Only 'fbx' is supported."}

    try:
        start_time = time.time()

        # Decode input mesh
        with tempfile.NamedTemporaryFile(suffix=".glb", delete=False) as input_file:
            input_file.write(base64.b64decode(mesh_b64))
            input_path = input_file.name

        # Create output path
        output_path = tempfile.mktemp(suffix=".fbx")

        try:
            # Run UniRig pipeline
            timings = run_unirig_pipeline(input_path, output_path, seed=seed)

            # Read and encode output
            with open(output_path, "rb") as f:
                output_b64 = base64.b64encode(f.read()).decode("utf-8")

            total_time = time.time() - start_time

            return {
                "output": output_b64,
                "format": "fbx",
                "processing_time": total_time,
                "timings": timings,
                "seed": seed,
            }

        finally:
            # Cleanup temp files
            if os.path.exists(input_path):
                os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)

    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc(),
        }


# Initialize on cold start
print("Initializing UniRig handler...")
try:
    load_models()
    print("UniRig models loaded successfully!")
except Exception as e:
    print(f"Warning: Model pre-loading failed: {e}")
    print("Models will be loaded on first request.")

# Start RunPod serverless
runpod.serverless.start({"handler": handler})
