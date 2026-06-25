# Card 09 - Plug in Meshy / Tripo as external providers

Status: DEFERRED
Depends on: 01 (provider abstraction), 02 (URL transport)
Quality bar: Meshy-6 meshes (this *is* the fallback to guarantee it)

## Goal

Add Meshy and Tripo as Generate (and where available, Rig) providers that call their cloud REST APIs. This is the moment MeshMaker becomes a true router, not just a self-hosting wrapper.

## Why

The cheat code for the Meshy-6 quality bar: when self-hosted output can't match, route the job to the platform that can. Being model-agnostic is the differentiator - the user picks the best backend per job from one Blender UI. See ARCHITECTURE "backend swap rules" and REFERENCE section 1.

## Scope

- `meshmaker/providers/cloud.py`: `MeshyProvider`, `TripoProvider` calling their REST APIs with the user's own API key (entered in preferences).
- Map their responses to the standard `Asset{url, metadata}`.
- Register in the provider registry; they appear in the same Generate dropdown as the RunPod backends.

## Acceptance criteria

- With a Meshy/Tripo key configured, the user can generate via that backend and the result imports identically to a self-hosted one.
- Switching backend is a dropdown change, nothing else.

## Notes

This proves the abstraction against backends you don't control - the real test of the router design. Keep keys client-side in preferences (BYO-key model).
