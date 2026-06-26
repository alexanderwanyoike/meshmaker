# Card 01 - Provider abstraction

Status: DONE
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
- Do not add new provider dropdowns in the simplified build. Keep the existing Generate model selector for legacy Trellis/Hunyuan3D 2.1 until card 06 replaces it with the Fal Hunyuan3D path.

## Acceptance criteria

- Generating / rigging / animating / segmenting still works end-to-end, now routed through the provider layer.
- Adding a new provider is a single new class + a registry entry, no operator changes.
- Raw base64 response assumptions are isolated in `meshmaker/providers/runpod.py` (prepares for card 02 URL transport).

## Notes

Keep `api.py` stdlib-only (the addon ships without pip deps). The provider classes are thin; the transport (RunPod polling, later storage download) stays in `api.py`.

## Verification

- `python3 -m pytest -q`
- `python3 -m compileall meshmaker tests`
