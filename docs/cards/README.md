# Implementation Cards

Ordered plan for the simplified MeshMaker build. Keep the first useful pipeline small:
one Generate backend, one storage transport, and only the rig/motion work needed to make
that output usable.

## Now - smallest useful pipeline
- **01** - Provider abstraction (thin spine, no multi-generator UI)
- **02** - Provider-agnostic URL asset transport
- **06** - Add one hosted Generate backend: Fal Hunyuan3D v3/v3.1
- **05** - Texture preservation through the rig roundtrip, only if rigging degrades output
- **09** - Meshy provider spike (Generate first, Rig only after skeleton compatibility check)

## Backlog / not in the current slice
- **03** - Restructure repo into the 5 cores (do when it reduces friction)
- **04** - Raise old Trellis/Hunyuan3D 2.1 quality defaults (archived with old generators)
- **07** - Swap Rig backend MIA -> SkinTokens
- **08** - Expose Segment tuning knobs (P3-SAM)
- **10** - Build the Video -> Animation core (QuickMagic style)
- **11** - Looping + foot-contact cleanup (Cascadeur-grade)
- **12** - Addons backlog

## Status legend
Each card starts `Status: TODO`, unless it has been explicitly archived.
The active quality bar is: Fal Hunyuan3D output should be production-usable enough to
justify continuing the pipeline.
