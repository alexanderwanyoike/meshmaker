# MeshMaker - Vision

> The single source of truth. If you're coming back to this project and feel lost, read this file first. Companion docs: `ARCHITECTURE.md` (the how), `REFERENCE.md` (model/provider landscape), `cards/` (the implementation record).

## What MeshMaker is

**An open Blender frontend for generating 3D meshes from images.** You type a prompt or pick an image, MeshMaker sends the job to a hosted AI provider, and a textured mesh lands cleanly in your scene. Bring your own API key; nothing runs on your GPU.

MeshMaker is **Generate-only by design.** Rigging, animation, and part segmentation are deliberately out of scope - each is its own focused tool. Keeping MeshMaker to a single capability is what keeps it small, understandable, and easy to maintain.

## The quality bar (the north star)

One bar drives every decision: **generated meshes must look production-usable, not clay.** That is why MeshMaker calls hosted, state-of-the-art providers (Fal Hunyuan3D 3.1, Meshy) rather than maintaining its own GPU containers.

## How it works

Three steps, two of them optional:

1. **(Optional) Concept image.** A text prompt goes to Gemini, which returns a concept image you can iterate on. Or skip this and supply your own image file.
2. **Generate.** The image goes to the selected provider's image-to-3D API. Providers return a hosted GLB URL.
3. **Import.** MeshMaker downloads the GLB and imports it into the scene.

## Architecture in one breath

A thin **provider spine**: the Blender UI builds a typed `GenerateRequest`, the chosen `Provider` calls its cloud API and returns an `Asset` (a hosted GLB URL), and the client downloads and imports it. Adding a Generate provider is one class plus one registry line. See `ARCHITECTURE.md`.

## Providers

- **Fal - Hunyuan3D 3.1 Pro** (`fal-ai/hunyuan-3d/v3.1/pro/image-to-3d`): the default Generate backend.
- **Meshy - Image to 3D**: textured image-to-3D, the second provider.

More Generate providers may be added later. No other capabilities are planned for this tool.

## Roadmap

**Shipped**
- Provider spine (typed request, `Asset` URL, registry).
- URL asset transport (download hosted GLB, import into Blender).
- Fal Hunyuan3D 3.1 provider.
- Meshy provider.

**Next**
- Additional Generate providers as the need arises (each is one class + one registry line).
- Generate-side polish: face-count/PBR tuning, retexture, mesh variations.

**Out of scope (separate tools)**
- Rigging, text/video motion, part segmentation. The old RunPod containers for these live in git history if ever needed to seed those tools.

## Reference

- `ARCHITECTURE.md` - the technical spec: provider spine, repo layout, data flow.
- `REFERENCE.md` - the Generate model/provider landscape.
- `cards/` - the implementation record.

## Naming note

This project was called CharMaker and Motion Creator in earlier docs. **The name is MeshMaker.** Git history on `dev` retains the superseded docs if ever needed.
