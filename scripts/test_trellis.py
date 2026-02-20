#!/usr/bin/env python3
"""
Test client for Trellis2 RunPod endpoint.

Usage:
    python scripts/test_trellis.py input.png output.glb

Environment:
    RUNPOD_API_KEY: Your RunPod API key
    TRELLIS_ENDPOINT_ID: Your Trellis2 endpoint ID
"""

import argparse
import base64
import os
import sys
import time

import requests


def main():
    parser = argparse.ArgumentParser(description="Test Trellis2 RunPod endpoint")
    parser.add_argument("input_image", help="Path to input image (PNG, JPG, or WebP)")
    parser.add_argument("output_glb", help="Path for output GLB file")
    parser.add_argument("--resolution", type=int, default=512, choices=[512, 1024, 1536],
                        help="Generation resolution (default: 512)")
    parser.add_argument("--texture-size", type=int, default=2048, choices=[1024, 2048, 4096],
                        help="Output texture size (default: 2048)")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    parser.add_argument("--decimation", type=int, default=None,
                        help="Target face count for mesh decimation")
    parser.add_argument("--endpoint", help="RunPod endpoint ID (or set TRELLIS_ENDPOINT_ID)")
    parser.add_argument("--api-key", help="RunPod API key (or set RUNPOD_API_KEY)")
    args = parser.parse_args()

    # Get credentials
    api_key = args.api_key or os.environ.get("RUNPOD_API_KEY")
    endpoint_id = args.endpoint or os.environ.get("TRELLIS_ENDPOINT_ID")

    if not api_key:
        print("Error: RUNPOD_API_KEY not set", file=sys.stderr)
        sys.exit(1)
    if not endpoint_id:
        print("Error: TRELLIS_ENDPOINT_ID not set", file=sys.stderr)
        sys.exit(1)

    # Read and encode input image
    print(f"Reading {args.input_image}...")
    with open(args.input_image, "rb") as f:
        image_b64 = base64.b64encode(f.read()).decode("utf-8")

    # Build payload
    payload_input = {
        "image": image_b64,
        "resolution": args.resolution,
        "texture_size": args.texture_size,
    }
    if args.seed is not None:
        payload_input["seed"] = args.seed
    if args.decimation is not None:
        payload_input["decimation_target"] = args.decimation

    # Submit job
    print(f"Submitting to RunPod endpoint {endpoint_id}...")
    url = f"https://api.runpod.ai/v2/{endpoint_id}/runsync"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {"input": payload_input}

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
    if result.get("status") in ("IN_QUEUE", "IN_PROGRESS"):
        job_id = result["id"]
        print(f"Job queued: {job_id}, waiting...")

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

    # Extract output
    output = result.get("output", result)
    if "error" in output:
        print(f"Error: {output['error']}", file=sys.stderr)
        sys.exit(1)

    glb_b64 = output.get("glb")
    if not glb_b64:
        print(f"Error: No GLB in response: {list(output.keys())}", file=sys.stderr)
        sys.exit(1)

    # Save GLB
    print(f"Saving {args.output_glb}...")
    glb_bytes = base64.b64decode(glb_b64)
    with open(args.output_glb, "wb") as f:
        f.write(glb_bytes)

    # Print stats
    meta = output.get("metadata", {})
    print(f"\nSuccess!")
    print(f"  Total time:       {elapsed:.1f}s")
    if "generation_time" in meta:
        print(f"  Generation time:  {meta['generation_time']:.1f}s")
    if "export_time" in meta:
        print(f"  Export time:      {meta['export_time']:.1f}s")
    print(f"  Resolution:       {meta.get('resolution', args.resolution)}")
    print(f"  Texture size:     {meta.get('texture_size', args.texture_size)}")
    print(f"  Seed:             {meta.get('seed', 'n/a')}")
    print(f"  GLB size:         {len(glb_bytes) / 1024 / 1024:.2f} MB")
    print(f"  Output:           {args.output_glb}")


if __name__ == "__main__":
    main()
