# Card 12 - Addons backlog

Status: DEFERRED (parking lot - promote individual items to their own cards when picked up)
Depends on: the relevant core being solid
Quality bar: n/a (toppings, not cores)

## Goal

Track the addon features that sit on top of solid cores. None of these are the project; pull one out into its own card only when a core is done and the addon is the next priority.

## On Generate
- **Batch generation** - queue multiple images/prompts, generate in parallel.
- **Mesh variations** - N variants from one input (seed sweep).
- **AI retexturing** - re-texture an existing mesh from a prompt.
- **Texture upscaling** - RealESRGAN-style upscale of generated textures (a stub already exists in the Hunyuan Dockerfile).
- **Mesh editing** - prompt-driven edits to a generated mesh.
- **Props / environments** - extend generation beyond characters.

## On Motion
- **Animation library** - curated game-ready clips (idle/walk/run/jump/attack) built on the Motion core + looping.

## On Animate
- **Game-engine export** - clean FBX/GLB presets for Unity / Unreal / Godot (correct skeleton, scale, conventions).

## Cross-cutting
- **Clean mesh output / naming** - meaningful object names + collection organisation on import (instead of `geometry_0`).
- **Test harness** - CLI/integration tests for each container and the end-to-end pipeline.

## Differentiation (from REFERENCE, longer horizon)
- **LoRA fine-tune HY-Motion** for loopable, snappy, short game-motion clips - the cheapest real differentiator vs stock models (LoRA-MDM: few examples, ~12h on a 24GB GPU).
- **Multi-editor plugins** (Unity, Unreal, Godot) - thin clients over the same provider API, the Tripo playbook.

## Notes

Order is demand-driven, not fixed. The discipline: don't start an addon until the core under it hits its quality bar.
