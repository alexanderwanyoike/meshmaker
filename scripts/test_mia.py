#!/usr/bin/env python3
"""
Test client for Make It Animatable (MIA) RunPod endpoint.
GLB mesh -> FBX with Mixamo skeleton + skin weights.

Usage:
    # Direct GLB input:
    python scripts/test_mia.py input.glb output.fbx

    # Full pipeline from image (Trellis -> MIA):
    python scripts/test_mia.py --from-image character.jpg output.fbx

Environment:
    RUNPOD_API_KEY:      Your RunPod API key
    MIA_ENDPOINT_ID:     Your MIA endpoint ID
    TRELLIS_ENDPOINT_ID: Your Trellis2 endpoint ID (required for --from-image)
"""

import argparse
import base64
import json
import os
import sys
import tempfile
import time
import urllib.error
import urllib.request

from dotenv import load_dotenv

load_dotenv()


def submit_and_poll(api_key, endpoint_id, payload, label):
    """Submit a job to RunPod and poll until complete. Returns output dict."""
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
            break
        elif status == "FAILED":
            output = result.get("output", result)
            print(f"{label} job failed!", file=sys.stderr)
            if isinstance(output, dict) and "error" in output:
                print(f"  Error: {output['error']}", file=sys.stderr)
                if "traceback" in output:
                    print(output["traceback"], file=sys.stderr)
            else:
                print(json.dumps(result, indent=2), file=sys.stderr)
            sys.exit(1)
        else:
            print(f"  {status}... ({elapsed:.0f}s)")

    output = result.get("output", {})
    if isinstance(output, dict) and "error" in output:
        print(f"Error from {label}: {output['error']}", file=sys.stderr)
        if "traceback" in output:
            print(output["traceback"], file=sys.stderr)
        sys.exit(1)

    return output, time.time() - start_time


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


def run_mia(api_key, endpoint_id, glb_bytes):
    """Run MIA on GLB bytes, return FBX bytes and metadata."""
    print(f"\n[2/2] MIA: GLB -> Mixamo FBX")
    mesh_b64 = base64.b64encode(glb_bytes).decode("utf-8")
    payload = {"input": {"mesh": mesh_b64}}

    output, elapsed = submit_and_poll(api_key, endpoint_id, payload, "MIA")

    fbx_b64 = output.get("output")
    if not fbx_b64:
        print(f"Error: No FBX in MIA response: {list(output.keys())}", file=sys.stderr)
        sys.exit(1)

    fbx_bytes = base64.b64decode(fbx_b64)
    print(f"  Done in {elapsed:.1f}s")
    print(f"  Bones:           {output.get('bone_count', 'n/a')}")
    print(f"  Processing time: {output.get('processing_time', elapsed):.1f}s")

    return fbx_bytes, elapsed


def check_mixamo_bones(fbx_path):
    """Scan FBX bytes for mixamorig: bone names — no external deps needed."""
    with open(fbx_path, "rb") as f:
        content = f.read()
    has_mixamo = b"mixamorig" in content
    if has_mixamo:
        # Count approximate bone references
        count = content.count(b"mixamorig:")
        print(f"  Mixamo bones:    yes (found {count} references to 'mixamorig:')")
    else:
        print(f"  Mixamo bones:    NOT FOUND — output may be wrong skeleton")
    return has_mixamo


def main():
    parser = argparse.ArgumentParser(description="Test MIA RunPod endpoint")
    parser.add_argument("input", help="Input GLB file, or image path when using --from-image")
    parser.add_argument("output_fbx", help="Path for output FBX file")
    parser.add_argument("--from-image", action="store_true",
                        help="Run Trellis2 first to generate GLB from image")
    parser.add_argument("--endpoint", help="MIA RunPod endpoint ID (or set MIA_ENDPOINT_ID)")
    parser.add_argument("--trellis-endpoint", help="Trellis2 endpoint ID (or set TRELLIS_ENDPOINT_ID)")
    parser.add_argument("--api-key", help="RunPod API key (or set RUNPOD_API_KEY)")
    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("RUNPOD_API_KEY")
    mia_endpoint = args.endpoint or os.environ.get("MIA_ENDPOINT_ID")

    if not api_key:
        print("Error: RUNPOD_API_KEY not set", file=sys.stderr)
        sys.exit(1)
    if not mia_endpoint:
        print("Error: MIA_ENDPOINT_ID not set", file=sys.stderr)
        sys.exit(1)

    total_start = time.time()

    if args.from_image:
        trellis_endpoint = args.trellis_endpoint or os.environ.get("TRELLIS_ENDPOINT_ID")
        if not trellis_endpoint:
            print("Error: TRELLIS_ENDPOINT_ID not set (required for --from-image)", file=sys.stderr)
            sys.exit(1)

        glb_bytes = run_trellis(api_key, trellis_endpoint, args.input)

        # Optionally save the intermediate GLB
        glb_path = args.output_fbx.replace(".fbx", ".glb")
        with open(glb_path, "wb") as f:
            f.write(glb_bytes)
        print(f"  Saved intermediate GLB: {glb_path}")

    else:
        print(f"Reading {args.input}...")
        with open(args.input, "rb") as f:
            glb_bytes = f.read()

    fbx_bytes, mia_elapsed = run_mia(api_key, mia_endpoint, glb_bytes)

    print(f"\nSaving {args.output_fbx}...")
    with open(args.output_fbx, "wb") as f:
        f.write(fbx_bytes)

    total_elapsed = time.time() - total_start
    print(f"\nResults:")
    print(f"  FBX size:        {len(fbx_bytes)/1024:.0f} KB")
    check_mixamo_bones(args.output_fbx)
    print(f"  Total time:      {total_elapsed:.1f}s")
    print(f"  Output:          {args.output_fbx}")


if __name__ == "__main__":
    main()
