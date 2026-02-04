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
import os
import sys
import time

import requests


def main():
    parser = argparse.ArgumentParser(description="Test UniRig RunPod endpoint")
    parser.add_argument("input_glb", help="Path to input GLB mesh file")
    parser.add_argument("output_fbx", help="Path for output FBX file")
    parser.add_argument("--seed", type=int, default=12345, help="Random seed")
    parser.add_argument("--endpoint", help="RunPod endpoint ID (or set UNIRIG_ENDPOINT_ID)")
    parser.add_argument("--api-key", help="RunPod API key (or set RUNPOD_API_KEY)")
    args = parser.parse_args()

    # Get credentials
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

    # Submit job
    print(f"Submitting to RunPod endpoint {endpoint_id}...")
    url = f"https://api.runpod.ai/v2/{endpoint_id}/runsync"
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

    start_time = time.time()
    response = requests.post(url, json=payload, headers=headers, timeout=300)
    response.raise_for_status()
    result = response.json()

    # Check for errors
    if "error" in result:
        print(f"Error: {result['error']}", file=sys.stderr)
        if "traceback" in result:
            print(result["traceback"], file=sys.stderr)
        sys.exit(1)

    # Handle async response (job queued)
    if result.get("status") == "IN_QUEUE" or result.get("status") == "IN_PROGRESS":
        job_id = result["id"]
        print(f"Job queued: {job_id}, waiting...")

        # Poll for completion
        status_url = f"https://api.runpod.ai/v2/{endpoint_id}/status/{job_id}"
        while True:
            time.sleep(5)
            status_response = requests.get(status_url, headers=headers)
            status_response.raise_for_status()
            result = status_response.json()

            if result.get("status") == "COMPLETED":
                result = result.get("output", result)
                break
            elif result.get("status") == "FAILED":
                print(f"Job failed: {result}", file=sys.stderr)
                sys.exit(1)
            else:
                print(f"  Status: {result.get('status')}...")

    elapsed = time.time() - start_time

    # Extract output from response
    output = result.get("output", result)
    if "error" in output:
        print(f"Error: {output['error']}", file=sys.stderr)
        sys.exit(1)

    # Decode and save FBX
    fbx_b64 = output.get("output")
    if not fbx_b64:
        print(f"Error: No output in response: {output}", file=sys.stderr)
        sys.exit(1)

    print(f"Saving {args.output_fbx}...")
    with open(args.output_fbx, "wb") as f:
        f.write(base64.b64decode(fbx_b64))

    # Print stats
    print(f"\nSuccess!")
    print(f"  Total time: {elapsed:.1f}s")
    if "processing_time" in output:
        print(f"  Processing time: {output['processing_time']:.1f}s")
    if "timings" in output:
        for stage, t in output["timings"].items():
            print(f"    {stage}: {t:.1f}s")
    print(f"  Output: {args.output_fbx}")


if __name__ == "__main__":
    main()
