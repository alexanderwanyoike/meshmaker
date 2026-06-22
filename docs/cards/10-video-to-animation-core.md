# Card 10 - Build the Video -> Animation core (QuickMagic style)

Status: TODO
Depends on: 03 (video stub + shared retarget), 01 (provider abstraction)
Quality bar: Cascadeur-grade animation

## Goal

Build Core 5: video in, animated character out. The QuickMagic-style capability - the only genuinely net-new core.

## Why

It is the second motion source alongside text. Crucially it reuses the existing back half: monocular mocap produces a `Motion`, which flows through the same SMPL-H -> Mixamo retarget as HY-Motion. So most of the work is one new container, not a new pipeline.

## Scope

- New container `containers/video-mocap/` using a monocular human-motion-recovery model (GVHMR / TRAM / WHAM lineage). Input: video. Output: `Motion` in HY-Motion's shape (SMPL-H joints), URL transport.
- Register as a VIDEO_MOTION provider.
- Wire the `core/video/` stub (from card 03) to: upload video -> get Motion -> reuse shared retarget onto the selected rigged character -> import animated FBX.
- Hand/finger tracking if the chosen model supports it (QuickMagic's signature feature).

## Acceptance criteria

- A short input video produces an animated rigged character in Blender.
- Output is a clean Mixamo FBX usable as a Cascadeur/Blender starting point (no catastrophic foot-sliding).
- Reuses the retarget module with no duplication.

## Notes

Pick the mocap model on quality vs license vs VRAM. WHAM/TRAM/GVHMR are the current open lineage; re-check for newer at build time.
