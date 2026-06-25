# Card 03 - Restructure repo into the 5 cores

Status: DEFERRED
Depends on: 01 (providers exist to anchor the cores)
Quality bar: enables both (navigability, not quality directly)

## Goal

Reorganize the addon so the code matches VISION's vocabulary: five self-contained cores, plus a shared retarget module.

## Why

Tabs are currently named `mesh/`, `anim/`. The mental model is Generate/Segment/Rig/Motion/Video. Aligning names to concepts is what makes the project easy to return to.

## Scope

- Rename/move under `meshmaker/core/`:
  - `mesh/` -> `core/generate/`
  - `segment/` -> `core/segment/`
  - `rig/` -> `core/rig/`
  - `anim/` -> `core/motion/`
  - add `core/video/` (stub panel + operator, "coming soon", wired to no provider yet)
- Extract the SMPL-H -> Mixamo retarget logic into a shared `meshmaker/retarget/` (client side) mirroring `containers/hymotion/retarget_fbx.py`, so cores 4 and 5 share it.
- Update `__init__.py` tab registration and imports.

## Acceptance criteria

- Addon loads with five tabs: Generate, Segment, Rig, Motion, Video (Video shows a stub).
- All existing flows work under the new module paths.
- No duplicated retarget logic between motion and video.

## Notes

Pure restructure - no behaviour change beyond the new Video stub. Keep commits mechanical so the diff is easy to review.
