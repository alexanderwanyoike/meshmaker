# Card 06 - Add Pixal3D / Hunyuan3D 3.5 as Generate backends

Status: TODO
Depends on: 01 (provider abstraction), 02 (URL transport)
Quality bar: Meshy-6 meshes

## Goal

Add the newest generation models as providers and A/B them against Trellis2 to chase the Meshy-6 fidelity bar.

## Why

Pixal3D (SIGGRAPH 2026) is pixel-aligned - near-reconstruction fidelity to the input image, the main weakness of Trellis/Hunyuan. Hunyuan3D 3.5 brings sub-60s generation and up to 8K PBR. See REFERENCE section 1.

## Scope

- New container `containers/pixal3d/` with a handler matching the Generate contract (image -> URL to GLB, URL transport from day one).
- Optionally upgrade the Hunyuan container to 3.5.
- Register both as Generate providers (card 01).
- Build a small A/B harness: same input image through Trellis2 / Pixal3D / Hunyuan3D 3.5, compare fidelity + texture quality side by side.

## Acceptance criteria

- User can pick the Generate backend from the panel dropdown.
- Documented A/B comparison on a handful of reference images showing where each model wins.
- At least one configuration that subjectively matches Meshy 6 on typical inputs.

## Notes

Don't delete Trellis2 - keep it as a fast/baseline option. The router's value is choice per input.
