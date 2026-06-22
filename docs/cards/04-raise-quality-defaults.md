# Card 04 - Raise quality defaults

Status: TODO
Depends on: 02 (transport ceiling must be gone first)
Quality bar: Meshy-6 meshes

## Goal

Now that assets travel by URL, raise the conservative generation defaults that were only low to fit the 20MB response.

## Why

Defaults were tuned for the transport limit, not for quality: Trellis `resolution=512`, `steps=12`, `texture_size=1024`; Hunyuan `octree_resolution=384`. This is free quality once card 02 lands.

## Scope

- Trellis2: default `resolution=1024`, raise `steps`, allow `texture_size` up to 4096.
- Hunyuan3D: default `octree_resolution=512`, keep `num_inference_steps`/`guidance` sane.
- Expose these in the Generate panel as quality presets (Draft / Standard / High) so users trade speed vs fidelity explicitly.
- Re-check decimation target (currently 100k) - make it a preset-linked value, not a hard cap.

## Acceptance criteria

- "High" preset produces visibly higher fidelity than the old defaults on the same input image.
- Generation time is acceptable per preset and documented.
- No regression in import.

## Notes

This card is where you first eyeball progress toward the Meshy-6 bar with your *existing* models, before adding new ones (card 06).
