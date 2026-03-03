"""
RunPod Serverless Handler for Hunyuan3D 2.1

Generates 3D GLB models from images or text prompts using Tencent's Hunyuan3D 2.1.
Shape model (3.3B) generates geometry, Paint model (2B) textures it.
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

# Add Hunyuan3D to path
HUNYUAN3D_DIR = "/app/hunyuan3d"
sys.path.insert(0, HUNYUAN3D_DIR)

# Configuration
VOLUME_PATH = os.environ.get("VOLUME_PATH", "/runpod-volume")
SHAPE_MODEL = "tencent/Hunyuan3D-2.1"
PAINT_MODEL = "tencent/Hunyuan3D-2.1"

# Global pipeline references
shape_pipeline = None
paint_pipeline = None


def load_model():
    """Load Shape and Paint pipelines."""
    global shape_pipeline, paint_pipeline

    if shape_pipeline is not None and paint_pipeline is not None:
        return shape_pipeline, paint_pipeline

    os.chdir(HUNYUAN3D_DIR)
    import torch

    # Load Shape pipeline (3.3B params)
    if shape_pipeline is None:
        print(f"Loading Shape pipeline from {SHAPE_MODEL}...")
        start_time = time.time()

        from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline

        shape_pipeline = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
            SHAPE_MODEL,
            subfolder="hunyuan3d-dit-v2-1",
            torch_dtype=torch.float16,
        )
        shape_pipeline = shape_pipeline.to("cuda")

        load_time = time.time() - start_time
        print(f"Shape pipeline loaded in {load_time:.2f}s")

    # Load Paint pipeline (2B params)
    if paint_pipeline is None:
        print(f"Loading Paint pipeline from {PAINT_MODEL}...")
        start_time = time.time()

        from hy3dgen.texgen import Hunyuan3DPaintPipeline

        paint_pipeline = Hunyuan3DPaintPipeline.from_pretrained(
            PAINT_MODEL,
            subfolder="hunyuan3d-paint-v2-1",
            torch_dtype=torch.float16,
        )
        paint_pipeline = paint_pipeline.to("cuda")

        load_time = time.time() - start_time
        print(f"Paint pipeline loaded in {load_time:.2f}s")

    return shape_pipeline, paint_pipeline


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
        print("Downloading image from URL...")
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
        background = Image.new("RGB", image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[3])
        image = background
    elif image.mode != "RGB":
        image = image.convert("RGB")

    return image


def generate_3d(
    image_input: str | None = None,
    text: str | None = None,
    seed: int | None = None,
    texture: bool = True,
) -> dict[str, Any]:
    """
    Generate a 3D GLB model from an input image or text prompt.

    Args:
        image_input: Base64-encoded image or URL (optional if text provided)
        text: Text prompt for text-to-3D (optional if image provided)
        seed: Random seed for reproducibility
        texture: Whether to apply texture via Paint model (default True)

    Returns:
        Dictionary with base64-encoded GLB and metadata
    """
    global shape_pipeline, paint_pipeline

    if shape_pipeline is None or paint_pipeline is None:
        load_model()

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

    generator = torch.Generator(device="cuda").manual_seed(seed)

    # Decode input image if provided
    image = None
    if image_input:
        print("Decoding input image...")
        image = decode_image(image_input)
        print(f"Image size: {image.size}, mode: {image.mode}")

    mode = "image-to-3D" if image is not None else "text-to-3D"
    print(f"Generating 3D model ({mode})...")
    print(f"  Seed: {seed}")
    print(f"  Texture: {texture}")
    if text:
        print(f"  Prompt: {text}")

    start_time = time.time()

    # Shape generation
    print("Running shape generation...")
    shape_start = time.time()

    shape_kwargs = dict(generator=generator)
    if image is not None:
        shape_kwargs["image"] = image
    if text:
        shape_kwargs["prompt"] = text

    mesh = shape_pipeline(**shape_kwargs)

    shape_time = time.time() - shape_start
    print(f"Shape generation completed in {shape_time:.2f}s")

    # Texture generation (Paint)
    if texture and paint_pipeline is not None:
        print("Running texture generation...")
        paint_start = time.time()

        paint_kwargs = dict(mesh=mesh)
        if image is not None:
            paint_kwargs["image"] = image

        mesh = paint_pipeline(mesh, image=image if image is not None else None)

        paint_time = time.time() - paint_start
        print(f"Texture generation completed in {paint_time:.2f}s")
    else:
        paint_time = 0.0

    # Export to GLB
    print("Exporting to GLB...")
    export_start = time.time()

    with tempfile.NamedTemporaryFile(suffix=".glb", delete=False) as tmp:
        tmp_path = tmp.name

    mesh.export(tmp_path)

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
        print(
            f"WARNING: Base64 output is {b64_mb:.1f} MB "
            "- may exceed RunPod sync limit (~20MB)"
        )

    total_time = time.time() - start_time
    print(f"Total generation time: {total_time:.2f}s")

    return {
        "glb": glb_base64,
        "metadata": {
            "seed": seed,
            "mode": mode,
            "texture": texture,
            "shape_time": round(shape_time, 2),
            "paint_time": round(paint_time, 2),
            "export_time": round(export_time, 2),
            "processing_time": round(total_time, 2),
            "glb_size_bytes": len(glb_bytes),
            "model": SHAPE_MODEL,
        },
    }


def handler(job: dict) -> dict:
    """RunPod serverless handler."""
    job_input = job.get("input", {})

    # Get inputs - either image or text is required
    image_input = job_input.get("image")
    text = job_input.get("text")

    if not image_input and not text:
        return {"error": "Missing required field: provide 'image' (base64/URL) or 'text' (prompt), or both"}

    # Extract parameters
    params = {
        "image_input": image_input,
        "text": text,
        "seed": job_input.get("seed"),
        "texture": job_input.get("texture", True),
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
print("Initializing Hunyuan3D 2.1 handler...")
try:
    load_model()
    print("Models loaded successfully!")
except Exception as e:
    print(f"Warning: Model pre-loading failed: {e}")
    print("Models will be loaded on first request.")

# Start RunPod serverless
runpod.serverless.start({"handler": handler})
