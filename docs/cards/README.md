# Implementation Cards

Ordered plan for the simplified MeshMaker build. Keep the first useful pipeline small:
one Generate backend, one storage transport, and only the rig/motion work needed to make
that output usable.

## Now - smallest useful pipeline
- **01** - Provider abstraction (thin spine, no multi-generator UI)
- **02** - Fix the transport ceiling with R2/object-storage URLs
- **06** - Replace Generate with one backend: Hunyuan3D 3.5
- **05** - Texture preservation through the rig roundtrip, only if rigging degrades output

## Deferred / archived for now
- **03** - Restructure repo into the 5 cores (defer until it reduces friction)
- **04** - Raise old Trellis/Hunyuan3D 2.1 quality defaults (archived with old generators)
- **07** - Swap Rig backend MIA -> SkinTokens
- **08** - Expose Segment tuning knobs (P3-SAM)
- **09** - Plug in Meshy / Tripo as external providers
- **10** - Build the Video -> Animation core (QuickMagic style)
- **11** - Looping + foot-contact cleanup (Cascadeur-grade)
- **12** - Addons backlog

## Status legend
Each card starts `Status: TODO`, unless it has been explicitly deferred or archived.
The active quality bar is: Hunyuan3D 3.5 output should be production-usable enough to
justify continuing the pipeline.
