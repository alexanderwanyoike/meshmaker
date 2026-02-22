#!/usr/bin/env python3
"""
Test client for HyMotion RunPod endpoint.

Usage:
    # With character FBX (retargeting path - returns animated FBX):
    python scripts/test_hymotion.py "walk forward" output.fbx --character-fbx rigged.fbx

    # Without character FBX (raw motion data - returns NPZ):
    python scripts/test_hymotion.py "walk forward" output.npz

Environment:
    RUNPOD_API_KEY: Your RunPod API key
    HYMOTION_ENDPOINT_ID: Your HyMotion endpoint ID
"""

import argparse
import base64
import io
import os
from dotenv import load_dotenv

load_dotenv()
import sys
import time

import numpy as np
import requests


def decode_numpy_arrays(motion_data: dict) -> dict:
    """Decode base64-encoded numpy arrays from HyMotion output."""
    decoded = {}
    for key, value in motion_data.items():
        if isinstance(value, dict) and "data" in value and "dtype" in value and "shape" in value:
            arr = np.frombuffer(
                base64.b64decode(value["data"]),
                dtype=value["dtype"],
            ).reshape(value["shape"])
            decoded[key] = arr
        elif not isinstance(value, dict):
            # Keep scalar values (fps, duration, num_frames, etc.)
            decoded[key] = value
    return decoded


def main():
    parser = argparse.ArgumentParser(description="Test HyMotion RunPod endpoint")
    parser.add_argument("prompt", help="Animation description (e.g. 'person walking forward')")
    parser.add_argument("output_file", help="Output path (.fbx with --character-fbx, .npz otherwise)")
    parser.add_argument("--character-fbx", metavar="PATH",
                        help="Path to rigged FBX for retargeting. Without this, returns raw NPZ motion data.")
    parser.add_argument("--duration", type=float, default=4.0,
                        help="Animation duration in seconds (default: 4.0)")
    parser.add_argument("--fps", type=int, default=30,
                        help="Frames per second (default: 30)")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    parser.add_argument("--guidance-scale", type=float, default=7.5,
                        help="Classifier-free guidance scale (default: 7.5)")
    parser.add_argument("--steps", type=int, default=50,
                        help="Number of inference steps (default: 50)")
    parser.add_argument("--endpoint", help="RunPod endpoint ID (or set HYMOTION_ENDPOINT_ID)")
    parser.add_argument("--api-key", help="RunPod API key (or set RUNPOD_API_KEY)")
    args = parser.parse_args()

    # Get credentials
    api_key = args.api_key or os.environ.get("RUNPOD_API_KEY")
    endpoint_id = args.endpoint or os.environ.get("HYMOTION_ENDPOINT_ID")

    if not api_key:
        print("Error: RUNPOD_API_KEY not set", file=sys.stderr)
        sys.exit(1)
    if not endpoint_id:
        print("Error: HYMOTION_ENDPOINT_ID not set", file=sys.stderr)
        sys.exit(1)

    # Build payload
    payload_input = {
        "prompt": args.prompt,
        "duration": args.duration,
        "fps": args.fps,
        "guidance_scale": args.guidance_scale,
        "num_inference_steps": args.steps,
    }
    if args.seed is not None:
        payload_input["seed"] = args.seed

    # Optionally attach character FBX for retargeting
    if args.character_fbx:
        print(f"Reading character FBX: {args.character_fbx}...")
        with open(args.character_fbx, "rb") as f:
            payload_input["character_fbx"] = base64.b64encode(f.read()).decode("utf-8")

    # Submit job
    print(f"Submitting to RunPod endpoint {endpoint_id}...")
    print(f"  Prompt:   \"{args.prompt}\"")
    print(f"  Duration: {args.duration}s @ {args.fps} FPS")
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
        if "traceback" in output:
            print(output["traceback"], file=sys.stderr)
        sys.exit(1)

    meta = output.get("metadata", {})

    if args.character_fbx:
        # Retargeting path: save animated FBX
        fbx_b64 = output.get("animated_fbx")
        if not fbx_b64:
            print(f"Error: No animated_fbx in response: {list(output.keys())}", file=sys.stderr)
            sys.exit(1)

        fbx_bytes = base64.b64decode(fbx_b64)
        print(f"Saving {args.output_file}...")
        with open(args.output_file, "wb") as f:
            f.write(fbx_bytes)

        print(f"\nSuccess! (animated FBX)")
        print(f"  Total time:       {elapsed:.1f}s")
        if "generation_time" in meta:
            print(f"  Generation time:  {meta['generation_time']:.1f}s")
        print(f"  Prompt:           \"{meta.get('prompt', args.prompt)}\"")
        print(f"  Duration:         {meta.get('duration', args.duration)}s")
        print(f"  Frames:           {meta.get('num_frames', 'n/a')}")
        print(f"  Seed:             {meta.get('seed', 'n/a')}")
        print(f"  File size:        {len(fbx_bytes) / 1024 / 1024:.2f} MB")
        print(f"  Output:           {args.output_file}")

    else:
        # Raw motion path: decode numpy arrays and save NPZ
        motion_data = output.get("motion_data")
        if not motion_data:
            print(f"Error: No motion_data in response: {list(output.keys())}", file=sys.stderr)
            sys.exit(1)

        print("Decoding motion arrays...")
        arrays = decode_numpy_arrays(motion_data)

        # Separate numpy arrays from scalar metadata
        np_arrays = {k: v for k, v in arrays.items() if isinstance(v, np.ndarray)}
        scalars = {k: v for k, v in arrays.items() if not isinstance(v, np.ndarray)}

        print(f"Saving {args.output_file}...")
        np.savez(args.output_file, **np_arrays)

        print(f"\nSuccess! (raw motion NPZ)")
        print(f"  Total time:       {elapsed:.1f}s")
        if "generation_time" in meta:
            print(f"  Generation time:  {meta['generation_time']:.1f}s")
        print(f"  Prompt:           \"{meta.get('prompt', args.prompt)}\"")
        print(f"  Duration:         {scalars.get('duration', meta.get('duration', args.duration))}s")
        print(f"  Frames:           {scalars.get('num_frames', meta.get('num_frames', 'n/a'))}")
        print(f"  Seed:             {meta.get('seed', 'n/a')}")
        print(f"  Arrays saved:")
        for name, arr in np_arrays.items():
            print(f"    {name}: shape={arr.shape}, dtype={arr.dtype}")
        print(f"  Output:           {args.output_file}")


if __name__ == "__main__":
    main()
