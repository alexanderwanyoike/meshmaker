"""
RunPod Serverless Handler for Trellis 2 (TRELLIS.2-4B)

Generates 3D GLB models from images using Microsoft's TRELLIS.2-4B model.
"""

import os
import sys
import io
import base64
import time
import tempfile
from typing import Any

import requests
import runpod

# Add Trellis 2 to path
TRELLIS_DIR = "/app/trellis2"
sys.path.insert(0, TRELLIS_DIR)

# Configuration
VOLUME_PATH = os.environ.get("VOLUME_PATH", "/runpod-volume")
MODEL_NAME = "microsoft/TRELLIS.2-4B"

# Global pipeline reference
pipeline = None


def load_model():
    """Load Trellis 2 pipeline."""
    global pipeline

    if pipeline is not None:
        return pipeline

    print(f"Loading {MODEL_NAME}...")
    start_time = time.time()

    # Change to trellis directory so relative paths work
    os.chdir(TRELLIS_DIR)

    import torch
    import trellis2.pipelines

    # Load the pipeline - it will download weights to HF_HOME on first run
    pipeline = trellis2.pipelines.Trellis2ImageTo3DPipeline.from_pretrained(MODEL_NAME)
    pipeline.cuda()

    load_time = time.time() - start_time
    print(f"Model loaded in {load_time:.2f}s")

    return pipeline


def decode_image(image_input: str):
    """Decode image from base64 string or URL.

    Args:
        image_input: Either a base64-encoded image string or a URL

    Returns:
        PIL Image object
    """
    from PIL import Image

    # Check if it's a URL
    if image_input.startswith(("http://", "https://")):
        print(f"Downloading image from URL...")
        response = requests.get(image_input, timeout=30)
        response.raise_for_status()
        image_data = response.content
    else:
        # Assume base64
        # Handle data URL format (data:image/png;base64,...)
        if image_input.startswith("data:"):
            image_input = image_input.split(",", 1)[1]
        image_data = base64.b64decode(image_input)

    image = Image.open(io.BytesIO(image_data))

    # Convert to RGB if necessary (remove alpha channel)
    if image.mode == "RGBA":
        # Create white background
        background = Image.new("RGB", image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[3])
        image = background
    elif image.mode != "RGB":
        image = image.convert("RGB")

    return image


def generate_3d(
    image_input: str,
    resolution: int = 512,
    seed: int | None = None,
    decimation_target: int = 100_000,
    texture_size: int = 1024,
    steps: int = 12,
    sparse_steps: int | None = None,
    shape_steps: int | None = None,
    tex_steps: int | None = None,
    sparse_guidance: float = 7.5,
    shape_guidance: float = 7.5,
    tex_guidance: float = 1.0,
) -> dict[str, Any]:
    """
    Generate a 3D GLB model from an input image.

    Args:
        image_input: Base64-encoded image or URL
        resolution: Generation resolution (512, 1024, or 1536)
        seed: Random seed for reproducibility
        decimation_target: Target number of faces for mesh decimation (default: 100k)
        texture_size: Output texture resolution (1024, 2048, or 4096). Default 1024
            to keep GLB under ~15MB for RunPod sync response limits.

    Returns:
        Dictionary with base64-encoded GLB and metadata
    """
    global pipeline

    if pipeline is None:
        load_model()

    # Validate resolution
    if resolution not in (512, 1024, 1536):
        resolution = 512
        print(f"Invalid resolution, using default: {resolution}")

    # Validate texture size
    if texture_size not in (1024, 2048, 4096):
        texture_size = 1024
        print(f"Invalid texture_size, using default: {texture_size}")

    # Set random seed
    if seed is None:
        seed = int(time.time()) % 2**32

    import torch
    import random
    import numpy as np
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    # Decode input image
    print("Decoding input image...")
    image = decode_image(image_input)
    print(f"Image size: {image.size}, mode: {image.mode}")

    print(f"Generating 3D model...")
    print(f"  Resolution: {resolution}")
    print(f"  Seed: {seed}")
    print(f"  Texture size: {texture_size}")
    if decimation_target:
        print(f"  Decimation target: {decimation_target}")

    start_time = time.time()

    # Resolve per-group step counts (fall back to global `steps` if not overridden).
    s_steps = sparse_steps if sparse_steps is not None else steps
    h_steps = shape_steps if shape_steps is not None else steps
    t_steps = tex_steps if tex_steps is not None else steps
    print(f"  Steps: sparse={s_steps} shape={h_steps} tex={t_steps}")
    print(f"  Guidance: sparse={sparse_guidance} shape={shape_guidance} tex={tex_guidance}")

    # Run the pipeline
    # pipeline.run() returns a list of MeshWithVoxel objects
    outputs = pipeline.run(
        image,
        seed=seed,
        sparse_structure_sampler_params={
            "steps": s_steps,
            "guidance_strength": sparse_guidance,
            "guidance_rescale": 0.7,
            "rescale_t": 5.0,
        },
        shape_slat_sampler_params={
            "steps": h_steps,
            "guidance_strength": shape_guidance,
            "guidance_rescale": 0.5,
            "rescale_t": 3.0,
        },
        tex_slat_sampler_params={
            "steps": t_steps,
            "guidance_strength": tex_guidance,
            "guidance_rescale": 0.0,
            "rescale_t": 3.0,
        },
    )

    generation_time = time.time() - start_time
    print(f"3D generation completed in {generation_time:.2f}s")
    print(f"outputs type: {type(outputs)}, len: {len(outputs) if hasattr(outputs, '__len__') else 'n/a'}")

    # Export to GLB
    print("Exporting to GLB...")
    export_start = time.time()

    import o_voxel

    # pipeline.run() returns a list of MeshWithVoxel; first element is the mesh
    mesh = outputs[0]

    # MeshWithVoxel has no .export() method. The correct workflow is:
    # 1. Optionally simplify the mesh (nvdiffrast limit is 16777216)
    # 2. Use o_voxel.postprocess.to_glb() to convert to a trimesh GLB scene
    # 3. Call .export() on the returned trimesh object

    # Apply nvdiffrast simplification limit
    mesh.simplify(16777216)

    # Apply decimation
    decimation = decimation_target if (decimation_target and decimation_target > 0) else 100_000

    # Save GLB to temporary file and read as bytes
    with tempfile.NamedTemporaryFile(suffix=".glb", delete=False) as tmp:
        tmp_path = tmp.name

    # Convert MeshWithVoxel to GLB via o_voxel postprocessing
    glb = o_voxel.postprocess.to_glb(
        vertices=mesh.vertices,
        faces=mesh.faces,
        attr_volume=mesh.attrs,
        coords=mesh.coords,
        attr_layout=mesh.layout,
        voxel_size=mesh.voxel_size,
        aabb=[[-0.5, -0.5, -0.5], [0.5, 0.5, 0.5]],
        decimation_target=decimation,
        texture_size=texture_size,
        remesh=True,
        remesh_band=1,
        remesh_project=0,
        verbose=True,
    )
    glb.export(tmp_path, extension_webp=True)

    with open(tmp_path, "rb") as f:
        glb_bytes = f.read()

    os.unlink(tmp_path)

    export_time = time.time() - export_start
    print(f"GLB export completed in {export_time:.2f}s")
    print(f"GLB size: {len(glb_bytes) / 1024 / 1024:.2f} MB")

    # Encode GLB as base64
    glb_base64 = base64.b64encode(glb_bytes).decode("utf-8")

    # Warn if output exceeds RunPod sync response limit (~20MB; base64 adds ~33%)
    b64_mb = len(glb_base64) / 1024 / 1024
    if b64_mb > 15:
        print(f"WARNING: Base64 output is {b64_mb:.1f} MB — may exceed RunPod sync limit (~20MB)")

    total_time = time.time() - start_time
    print(f"Total generation time: {total_time:.2f}s")

    return {
        "glb": glb_base64,
        "metadata": {
            "resolution": resolution,
            "seed": seed,
            "generation_time": round(generation_time, 2),
            "export_time": round(export_time, 2),
            "total_time": round(total_time, 2),
            "glb_size_bytes": len(glb_bytes),
            "texture_size": texture_size,
            "decimation_target": decimation_target,
            "model": MODEL_NAME,
        },
    }


def handler(job: dict) -> dict:
    """RunPod serverless handler."""
    job_input = job.get("input", {})

    # Validate required input
    image_input = job_input.get("image")
    if not image_input:
        return {"error": "Missing required field: image"}

    # Extract parameters
    params = {
        "image_input": image_input,
        "resolution": job_input.get("resolution", 512),
        "seed": job_input.get("seed"),
        "decimation_target": job_input.get("decimation_target", 100_000),
        "texture_size": job_input.get("texture_size", 1024),
        "steps": job_input.get("steps", 12),
        "sparse_steps": job_input.get("sparse_steps"),
        "shape_steps": job_input.get("shape_steps"),
        "tex_steps": job_input.get("tex_steps"),
        "sparse_guidance": job_input.get("sparse_guidance", 7.5),
        "shape_guidance": job_input.get("shape_guidance", 7.5),
        "tex_guidance": job_input.get("tex_guidance", 1.0),
    }

    try:
        result = generate_3d(**params)
        return result

    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc(),
        }


# Load model on cold start
print("Initializing Trellis 2 handler...")
try:
    load_model()
    print("Model loaded successfully!")
except Exception as e:
    print(f"Warning: Model pre-loading failed: {e}")
    print("Model will be loaded on first request.")

# Start RunPod serverless
runpod.serverless.start({"handler": handler})
