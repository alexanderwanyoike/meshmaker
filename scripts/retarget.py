#!/usr/bin/env python3
"""
Retarget SMPL-H motion (NPZ) to a Mixamo-rigged FBX character.

Uses the vendored retarget_fbx.py from hy-motion-fbx-exporter which does
proper FK, offset quaternions, and world-to-local conversion.

Usage:
    python scripts/retarget.py test_output/motion.npz test_output/character.fbx test_output/retargeted.fbx
    python scripts/retarget.py motion.npz char.fbx out.fbx --yaw 90 --scale 1.0
"""

import argparse
import sys
import os

# Add scripts/ to path so we can import the vendored module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from retarget_fbx import retarget_fbx


def main():
    parser = argparse.ArgumentParser(
        description="Retarget SMPL-H motion (NPZ) to a Mixamo-rigged FBX character"
    )
    parser.add_argument("npz", help="Path to NPZ with SMPL-H motion data")
    parser.add_argument("fbx", help="Path to rigged FBX character (Mixamo skeleton)")
    parser.add_argument("output", help="Output FBX path")
    parser.add_argument(
        "--yaw", type=float, default=0.0,
        help="Yaw rotation offset in degrees (default: 0)"
    )
    parser.add_argument(
        "--scale", type=float, default=None,
        help="Force scale factor (default: auto-detect from skeleton)"
    )
    parser.add_argument(
        "--no-neutral-fingers", action="store_true",
        help="Disable neutral finger rest pose (use raw SMPL-H fingers)"
    )
    parser.add_argument(
        "--mapping", type=str, default=None,
        help="Path to custom bone mapping JSON file"
    )
    args = parser.parse_args()

    if not os.path.isfile(args.npz):
        print(f"Error: NPZ file not found: {args.npz}", file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(args.fbx):
        print(f"Error: FBX file not found: {args.fbx}", file=sys.stderr)
        sys.exit(1)

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)

    retarget_fbx(
        npz_path=args.npz,
        target_fbx_path=args.fbx,
        output_path=args.output,
        yaw_offset=args.yaw,
        force_scale=args.scale,
        neutral_fingers=not args.no_neutral_fingers,
        mapping_file=args.mapping,
    )
    print(f"Output: {args.output}")


if __name__ == "__main__":
    main()
