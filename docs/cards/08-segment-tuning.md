# Card 08 - Expose Segment tuning knobs

Status: DEFERRED
Depends on: 01 (provider abstraction)
Quality bar: n/a (usability of the Segment core)

## Goal

Make part segmentation controllable instead of one-shot, so it produces art-directable parts rather than fixed semantic regions.

## Why

The P3-SAM handler currently calls `predict_aabb` with zero user-facing parameters (`containers/hunyuan3d-part/handler.py`). Users can't tune granularity, so results feel "not effective." P3-SAM is semantic, not art-directed, by default.

## Scope

- Surface P3-SAM's internal controls (threshold / granularity / max parts, whatever the API exposes) in the SegmentRequest and the panel.
- Return per-part metadata (face count, bbox) so the user can cull tiny/garbage parts.
- Optionally a "merge small parts" post-step.

## Acceptance criteria

- User can re-run segmentation at coarser/finer granularity from the panel and see different part counts.
- Tiny/degenerate parts can be filtered out before import.

## Notes

Lower priority than the generation/rig/motion cores. Newer generators (e.g. Pixal3D scene synthesis) increasingly give object-separated output for free - don't over-invest here.
