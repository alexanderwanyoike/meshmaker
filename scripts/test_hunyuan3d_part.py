#!/usr/bin/env python3
"""
Test client for Hunyuan3D-Part (P3-SAM) RunPod endpoint.
Segments a GLB mesh into semantic parts.

Usage:
    # Segment a mesh:
    python scripts/test_hunyuan3d_part.py input.glb output_dir/

    # Full pipeline from image (Trellis -> segment):
    python scripts/test_hunyuan3d_part.py --from-image character.png output_dir/

Environment:
    RUNPOD_API_KEY:          Your RunPod API key
    SEGMENT_ENDPOINT_ID:     Your Hunyuan3D-Part endpoint ID
    TRELLIS_ENDPOINT_ID:     Your Trellis2 endpoint ID (for --from-image)
"""

import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request

from dotenv import load_dotenv

load_dotenv()


def submit_and_poll(api_key, endpoint_id, payload, label):
    """Submit a job to RunPod and poll until complete."""
    url = f"https://api.runpod.ai/v2/{endpoint_id}/run"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    start_time = time.time()
    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read().decode("utf-8"))

    if "error" in result:
        print(f"Error submitting {label}: {result['error']}", file=sys.stderr)
        sys.exit(1)

    job_id = result.get("id")
    if not job_id:
        print(f"Error: No job ID in response: {result}", file=sys.stderr)
        sys.exit(1)

    print(f"  Job submitted: {job_id}")

    status_url = f"https://api.runpod.ai/v2/{endpoint_id}/status/{job_id}"
    while True:
        time.sleep(5)
        try:
            status_req = urllib.request.Request(status_url, headers=headers)
            with urllib.request.urlopen(status_req, timeout=90) as resp:
                result = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            print(f"  Poll error ({e}), retrying...")
            continue

        status = result.get("status")
        elapsed = time.time() - start_time
        if status == "COMPLETED":
            output = result.get("output", {})
            if isinstance(output, dict) and "error" in output:
                print(f"Error: {output['error']}", file=sys.stderr)
                if "traceback" in output:
                    print(output["traceback"], file=sys.stderr)
                sys.exit(1)
            return output, elapsed
        elif status == "FAILED":
            output = result.get("output", result)
            print(f"{label} job failed!", file=sys.stderr)
            if isinstance(output, dict) and "error" in output:
                print(f"  Error: {output['error']}", file=sys.stderr)
                if "traceback" in output:
                    print(output["traceback"], file=sys.stderr)
            else:
                print(json.dumps(result, indent=2, default=str), file=sys.stderr)
            sys.exit(1)
        else:
            print(f"  {status}... ({elapsed:.0f}s)")


def run_trellis(api_key, endpoint_id, image_path):
    """Run Trellis2 on an image, return GLB bytes."""
    print(f"\n[1/2] Trellis2: {image_path} -> GLB")
    with open(image_path, "rb") as f:
        image_b64 = base64.b64encode(f.read()).decode("utf-8")

    payload = {"input": {
        "image": image_b64,
        "texture_size": 1024,
        "resolution": 512,
    }}

    output, elapsed = submit_and_poll(api_key, endpoint_id, payload, "Trellis2")

    glb_b64 = output.get("glb")
    if not glb_b64:
        print(f"Error: No GLB in Trellis2 response: {list(output.keys())}", file=sys.stderr)
        sys.exit(1)

    glb_bytes = base64.b64decode(glb_b64)
    meta = output.get("metadata", {})
    print(f"  Done in {elapsed:.1f}s — {len(glb_bytes)/1024:.0f} KB GLB")
    if "seed" in meta:
        print(f"  Seed: {meta['seed']}")

    return glb_bytes


def main():
    parser = argparse.ArgumentParser(description="Test Hunyuan3D-Part (P3-SAM) RunPod endpoint")
    parser.add_argument("input", help="Input GLB file, or image path when using --from-image")
    parser.add_argument("output_dir", help="Directory for output part GLB files")
    parser.add_argument("--from-image", action="store_true",
                        help="Run Trellis2 first to generate GLB from image")
    parser.add_argument("--endpoint", help="Segment endpoint ID (or set SEGMENT_ENDPOINT_ID)")
    parser.add_argument("--trellis-endpoint", help="Trellis2 endpoint ID (or set TRELLIS_ENDPOINT_ID)")
    parser.add_argument("--api-key", help="RunPod API key (or set RUNPOD_API_KEY)")
    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("RUNPOD_API_KEY")
    segment_endpoint = args.endpoint or os.environ.get("SEGMENT_ENDPOINT_ID")

    if not api_key:
        print("Error: RUNPOD_API_KEY not set", file=sys.stderr)
        sys.exit(1)
    if not segment_endpoint:
        print("Error: SEGMENT_ENDPOINT_ID not set", file=sys.stderr)
        sys.exit(1)

    total_start = time.time()

    if args.from_image:
        trellis_endpoint = args.trellis_endpoint or os.environ.get("TRELLIS_ENDPOINT_ID")
        if not trellis_endpoint:
            print("Error: TRELLIS_ENDPOINT_ID not set (required for --from-image)", file=sys.stderr)
            sys.exit(1)

        glb_bytes = run_trellis(api_key, trellis_endpoint, args.input)

        # Save intermediate GLB
        os.makedirs(args.output_dir, exist_ok=True)
        intermediate_path = os.path.join(args.output_dir, "input_mesh.glb")
        with open(intermediate_path, "wb") as f:
            f.write(glb_bytes)
        print(f"  Saved intermediate GLB: {intermediate_path}")

        step_label = "[2/2] P3-SAM"
    else:
        print(f"Reading {args.input}...")
        with open(args.input, "rb") as f:
            glb_bytes = f.read()
        step_label = "P3-SAM"

    # Run segmentation
    print(f"\n{step_label}: GLB -> segmented parts")
    mesh_b64 = base64.b64encode(glb_bytes).decode("utf-8")
    payload = {"input": {"mesh": mesh_b64}}

    output, elapsed = submit_and_poll(api_key, segment_endpoint, payload, "P3-SAM")

    parts = output.get("parts", [])
    if not parts:
        print(f"Error: No parts in response: {list(output.keys())}", file=sys.stderr)
        sys.exit(1)

    # Save each part
    os.makedirs(args.output_dir, exist_ok=True)

    print(f"\nSaving {len(parts)} parts to {args.output_dir}/")
    for part in parts:
        part_name = part.get("name", "unknown")
        part_b64 = part.get("mesh")
        face_count = part.get("face_count", "?")

        if not part_b64:
            print(f"  {part_name}: no mesh data, skipping")
            continue

        part_bytes = base64.b64decode(part_b64)
        part_path = os.path.join(args.output_dir, f"{part_name}.glb")
        with open(part_path, "wb") as f:
            f.write(part_bytes)
        print(f"  {part_name}.glb — {len(part_bytes)/1024:.0f} KB, {face_count} faces")

    meta = output.get("metadata", {})
    total_elapsed = time.time() - total_start
    print(f"\nSuccess!")
    print(f"  Parts:            {meta.get('num_parts', len(parts))}")
    print(f"  Total faces:      {meta.get('total_faces', 'n/a')}")
    print(f"  Segmentation:     {elapsed:.1f}s")
    print(f"  Total time:       {total_elapsed:.1f}s")
    print(f"  Output dir:       {args.output_dir}")


if __name__ == "__main__":
    main()
