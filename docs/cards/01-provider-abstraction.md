# Card 01 - Provider abstraction

Status: TODO
Depends on: nothing (this is the spine; do it first)
Quality bar: enables both

## Goal

Introduce a capability -> provider abstraction so backends become swappable, and refactor the existing model integrations to sit behind it. This is the foundation every later card builds on.

## Why

Code is currently organized by model, with bespoke operators per handler. That is why adding/swapping a model feels like new work and the repo feels disorganized. A provider interface turns every future change into "new provider," "new capability," or "UI change."

## Scope

- Add `meshmaker/providers/`:
  - `base.py` - `Capability` enum (GENERATE, SEGMENT, RIG, MOTION, VIDEO_MOTION), `Provider` base class, typed request/response dataclasses, `Asset` (url + metadata, never base64).
  - `runpod.py` - one provider per existing container (Trellis2, Hunyuan3D, P3-SAM, MIA, HY-Motion) wrapping the current `api.call_runpod` flow.
  - `registry.py` - discovery: list providers, query "who supports capability X", resolve the user's chosen provider.
- Refactor the four Blender operators (mesh, rig, anim, segment) to call `registry.resolve(cap, choice).<capability>(req)` instead of hand-rolling payloads.
- Add a provider dropdown to each core's panel (defaults to the current model, so behaviour is unchanged).

## Acceptance criteria

- Generating / rigging / animating / segmenting still works end-to-end, now routed through the provider layer.
- Adding a new provider is a single new class + a registry entry, no operator changes.
- No raw base64 assumptions leak into the UI layer (prepares for card 02).

## Notes

Keep `api.py` stdlib-only (the addon ships without pip deps). The provider classes are thin; the transport (RunPod polling, later storage download) stays in `api.py`.
