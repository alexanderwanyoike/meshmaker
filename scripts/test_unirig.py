#!/usr/bin/env python3
"""
Test client for UniRig RunPod endpoint.

Usage:
    python scripts/test_unirig.py input.glb output.fbx

Environment:
    RUNPOD_API_KEY: Your RunPod API key
    UNIRIG_ENDPOINT_ID: Your UniRig endpoint ID
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


def main():
    parser = argparse.ArgumentParser(description="Test UniRig RunPod endpoint")
    parser.add_argument("input_glb", help="Path to input GLB mesh file")
    parser.add_argument("output_fbx", help="Path for output FBX file")
    parser.add_argument("--seed", type=int, default=12345, help="Random seed")
    parser.add_argument("--endpoint", help="RunPod endpoint ID (or set UNIRIG_ENDPOINT_ID)")
    parser.add_argument("--api-key", help="RunPod API key (or set RUNPOD_API_KEY)")
    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("RUNPOD_API_KEY")
    endpoint_id = args.endpoint or os.environ.get("UNIRIG_ENDPOINT_ID")

    if not api_key:
        print("Error: RUNPOD_API_KEY not set", file=sys.stderr)
        sys.exit(1)
    if not endpoint_id:
        print("Error: UNIRIG_ENDPOINT_ID not set", file=sys.stderr)
        sys.exit(1)

    # Read and encode input mesh
    print(f"Reading {args.input_glb}...")
    with open(args.input_glb, "rb") as f:
        mesh_b64 = base64.b64encode(f.read()).decode("utf-8")

    # Submit async job via /run
    print(f"Submitting to RunPod endpoint {endpoint_id}...")
    url = f"https://api.runpod.ai/v2/{endpoint_id}/run"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "input": {
            "mesh": mesh_b64,
            "format": "fbx",
            "seed": args.seed,
        }
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

    # Poll for completion
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
        if status == "COMPLETED":
            break
        elif status == "FAILED":
            output = result.get("output", result)
            print(f"Job failed!", file=sys.stderr)
            if isinstance(output, dict) and "error" in output:
                print(f"  Error: {output['error']}", file=sys.stderr)
                if "traceback" in output:
                    print(output["traceback"], file=sys.stderr)
            else:
                print(f"  Response: {json.dumps(result, indent=2)}", file=sys.stderr)
            sys.exit(1)
        else:
            elapsed = time.time() - start_time
            print(f"  {status}... ({elapsed:.0f}s)")

    elapsed = time.time() - start_time

    # Extract output
    output = result.get("output", {})
    if isinstance(output, str):
        # Entire output is the base64 FBX
        fbx_b64 = output
        output = {}
    elif isinstance(output, dict):
        if "error" in output:
            print(f"Error: {output['error']}", file=sys.stderr)
            if "traceback" in output:
                print(output["traceback"], file=sys.stderr)
            sys.exit(1)
        fbx_b64 = output.get("output")
    else:
        print(f"Error: Unexpected output format: {type(output)}", file=sys.stderr)
        sys.exit(1)

    if not fbx_b64:
        print(f"Error: No FBX data in response", file=sys.stderr)
        print(f"  Keys: {list(output.keys()) if isinstance(output, dict) else 'N/A'}", file=sys.stderr)
        sys.exit(1)

    # Save output
    print(f"Saving {args.output_fbx}...")
    with open(args.output_fbx, "wb") as f:
        f.write(base64.b64decode(fbx_b64))

    print(f"\nSuccess!")
    print(f"  Total time: {elapsed:.1f}s")
    if isinstance(output, dict):
        if "processing_time" in output:
            print(f"  Processing time: {output['processing_time']:.1f}s")
        if "timings" in output:
            for stage, t in output["timings"].items():
                print(f"    {stage}: {t:.1f}s")
    print(f"  Output: {args.output_fbx}")


if __name__ == "__main__":
    main()
