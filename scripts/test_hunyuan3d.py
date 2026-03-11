#!/usr/bin/env python3
"""
Test client for Hunyuan3D 2.1 RunPod endpoint.
Image-to-3D mesh generation.

Usage:
    python scripts/test_hunyuan3d.py input.png output.glb

Environment:
    RUNPOD_API_KEY:          Your RunPod API key
    HUNYUAN3D_ENDPOINT_ID:   Your Hunyuan3D 2.1 endpoint ID
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


def submit_and_poll(api_key, endpoint_id, payload):
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
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)

    job_id = result.get("id")
    if not job_id:
        print(f"Error: No job ID in response: {result}", file=sys.stderr)
        sys.exit(1)

    print(f"Job submitted: {job_id}")

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
            print(f"Job failed!", file=sys.stderr)
            if isinstance(output, dict) and "error" in output:
                print(f"  Error: {output['error']}", file=sys.stderr)
                if "traceback" in output:
                    print(output["traceback"], file=sys.stderr)
            else:
                print(json.dumps(result, indent=2, default=str), file=sys.stderr)
            sys.exit(1)
        else:
            print(f"  {status}... ({elapsed:.0f}s)")


def main():
    parser = argparse.ArgumentParser(description="Test Hunyuan3D 2.1 RunPod endpoint")
    parser.add_argument("input_image", help="Path to input image")
    parser.add_argument("output_glb", help="Path for output GLB file")
    parser.add_argument("--no-texture", action="store_true", help="Skip texture generation")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    parser.add_argument("--endpoint", help="RunPod endpoint ID (or set HUNYUAN3D_ENDPOINT_ID)")
    parser.add_argument("--api-key", help="RunPod API key (or set RUNPOD_API_KEY)")
    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("RUNPOD_API_KEY")
    endpoint_id = args.endpoint or os.environ.get("HUNYUAN3D_ENDPOINT_ID")

    if not api_key:
        print("Error: RUNPOD_API_KEY not set", file=sys.stderr)
        sys.exit(1)
    if not endpoint_id:
        print("Error: HUNYUAN3D_ENDPOINT_ID not set", file=sys.stderr)
        sys.exit(1)

    # Build payload
    print(f"Reading {args.input_image}...")
    with open(args.input_image, "rb") as f:
        payload_input = {
            "image": base64.b64encode(f.read()).decode("utf-8"),
            "texture": not args.no_texture,
        }

    if args.seed is not None:
        payload_input["seed"] = args.seed

    print("Submitting image-to-3D job to Hunyuan3D 2.1...")

    output, elapsed = submit_and_poll(api_key, endpoint_id, {"input": payload_input})

    glb_b64 = output.get("glb")
    if not glb_b64:
        print(f"Error: No GLB in response: {list(output.keys())}", file=sys.stderr)
        sys.exit(1)

    glb_bytes = base64.b64decode(glb_b64)

    print(f"Saving {args.output_glb}...")
    with open(args.output_glb, "wb") as f:
        f.write(glb_bytes)

    meta = output.get("metadata", {})
    print(f"\nSuccess!")
    print(f"  Mode:             {meta.get('mode', 'image-to-3D')}")
    print(f"  Total time:       {elapsed:.1f}s")
    if "shape_time" in meta:
        print(f"  Shape time:       {meta['shape_time']:.1f}s")
    if "paint_time" in meta:
        print(f"  Paint time:       {meta['paint_time']:.1f}s")
    print(f"  Seed:             {meta.get('seed', 'n/a')}")
    print(f"  Texture:          {meta.get('texture', not args.no_texture)}")
    print(f"  GLB size:         {len(glb_bytes) / 1024 / 1024:.2f} MB")
    print(f"  Output:           {args.output_glb}")


if __name__ == "__main__":
    main()
