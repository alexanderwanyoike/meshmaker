# MeshMaker - Reference

> The Generate (image -> mesh) landscape and the provider API contracts MeshMaker ships against. Background for `cards/`, not a to-do list. Last refreshed June 2026.

## Active providers

| Provider | Model | Endpoint | Auth | GLB field |
|---|---|---|---|---|
| **Fal** | Hunyuan3D 3.1 | `fal-ai/hunyuan-3d/v3.1/{tier}/image-to-3d` | `Authorization: Key <key>` | `model_urls.glb.url` / `model_glb.url` |
| **Fal** | Pixal3D | `fal-ai/pixal3d` | `Authorization: Key <key>` | `model_glb.url` |
| **Fal** | Tripo v2.5 | `tripo3d/tripo/v2.5/image-to-3d` | `Authorization: Key <key>` | `model_mesh.url` |
| **Fal** | Hyper3D Rodin | `fal-ai/hyper3d/rodin` | `Authorization: Key <key>` | `model_mesh.url` |
| **Meshy** | Image to 3D | `api.meshy.ai/openapi/v1/image-to-3d` | `Authorization: Bearer <key>` | `model_urls.glb` |

All accept the reference image as a base64 data URI (`data:image/png;base64,...`),
so no separate image upload is required. The four Fal models share one Fal API key
and one queue transport (`FalQueueProvider` in `providers/fal/queue.py`); only the endpoint, payload, and the
result's GLB field differ (`_fal_glb_url` handles all three output shapes).

### Fal (queue API)

All Fal models use the same queue mechanics:

- **Submit:** `POST https://queue.fal.run/{endpoint}`
  - returns: `{ request_id, status_url, response_url, cancel_url }`
- **Poll:** `GET <status_url>` -> `status` in `IN_QUEUE | IN_PROGRESS | COMPLETED`
- **Result:** `GET <response_url>` -> the model's output JSON (GLB field varies)

Per-model request bodies:

- **Hunyuan3D 3.1** `{ input_image_url, face_count (40k-1.5M), enable_pbr, generate_type }`. `tier` picks `pro` (quality) or `rapid` (fast/cheap). ~$0.375/gen, +$0.15 PBR. Result: `{ model_glb, model_urls: { glb, obj, fbx, usdz }, seed }`.
- **Pixal3D** `{ image_url, resolution (1024|1536), texture_size (1024|2048|4096), remesh, decimation_target }`. Pixel-aligned, high fidelity. ~$0.30 (1024p) / $0.42 (1536p). Result: `{ model_glb, seed }`.
- **Tripo v2.5** `{ image_url, texture (no|standard|HD), pbr, quad, face_limit }`. Fast, strong geometry. Result: `{ task_id, model_mesh, pbr_model, base_model }`.
- **Rodin** `{ input_image_urls[], geometry_file_format, quality (high|medium|low|extra-low), material (PBR|Shaded), tier (Regular|Sketch), hyper_mode }`. Premium quality. ~$0.40/gen, HighPack 3x. Result: `{ model_mesh, textures[] }`.

### Meshy (OpenAPI)

- **Create:** `POST https://api.meshy.ai/openapi/v1/image-to-3d`
  - body: `{ image_url, ai_model, should_texture, enable_pbr, target_polycount, target_formats, topology, ... }`
  - returns: `{ result: "<task_id>" }`
- **Poll:** `GET https://api.meshy.ai/openapi/v1/image-to-3d/{id}` -> `status` in `PENDING | IN_PROGRESS | SUCCEEDED | FAILED | CANCELED`
- **Result (on `SUCCEEDED`):** `{ model_urls: { glb, fbx, obj, ... }, texture_urls[], thumbnail_url, consumed_credits }`
- **Pricing:** $20/mo for ~1000 credits; image-to-3D with texture is ~30 credits.

## Generate model landscape (for future providers)

If another Generate provider is ever added, these are the candidates worth knowing:

| Model | Origin | License | Notes |
|---|---|---|---|
| **Hunyuan3D 3.1** (active, via Fal) | Tencent | Commercial API | Default. Strong geometry + PBR, hosted |
| **Pixal3D** (active, via Fal) | TencentARC | Commercial API | Pixel-aligned, high-fidelity texture. Fal-only |
| **Tripo v2.5** (active, via Fal) | VAST-AI | Commercial API | Fast, strong geometry; PBR/quad/HD texture |
| **Hyper3D Rodin** (active, via Fal) | Deemos | Commercial API | Premium quality; quality tiers, hyper mode |
| **Meshy-5/6** (active) | Meshy | Commercial API | Textured, fast, good all-rounder |
| **Trellis 2** | Microsoft | MIT | Strong geometry, darker textures. Self-host only |
| **Hunyuan3D 2.1** | Tencent | Permissive | Good PBR. Self-host only |
| **TripoSG / TripoSR** | VAST-AI | MIT | Shape-only (SG) or very fast previews (SR) |

Tripo and Rodin also have native APIs (platform.tripo3d.ai, Deemos) with newer
model versions (Tripo v3.1/P1, Rodin Gen-2). MeshMaker routes both through Fal to
reuse one key and one transport; a native client is only worth adding if a Fal-lagged
model version becomes a hard requirement.

**Takeaway:** prefer hosted APIs that return a GLB URL. Self-hosted models
(Trellis, Hunyuan 2.1) are only worth it if a hosted option fails the quality or
cost bar, and would mean re-introducing GPU infrastructure this tool deliberately
dropped.

## Positioning notes

- **Generate-only is the moat-by-focus.** MeshMaker is the cleanest possible "image in, Blender mesh out" front end. Routing across the best hosted providers from one UI is the value; it does not try to also be a rigging or animation tool.
- **BYO-key, adoption first.** Users bring their own Fal/Meshy keys. Free open-source addon now; a hosted "MeshMaker Go" key-less tier is a possible future, added last.
- **Don't innovate on pricing.** Credit-based SaaS is the proven model in this space; differentiate on product (provider coverage, Blender-native UX), not price.

## Sources

- [Fal Hunyuan3D 3.1 Pro](https://fal.ai/models/fal-ai/hunyuan-3d/v3.1/pro/image-to-3d/api) | [Fal queue API](https://fal.ai/docs/model-endpoints/queue)
- [Meshy Image to 3D](https://docs.meshy.ai/en/api/image-to-3d) | [Meshy pricing](https://www.meshy.ai/pricing)
- [Hunyuan3D 2.1](https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1) | [Trellis 2](https://github.com/microsoft/TRELLIS) | [Tripo](https://www.tripo3d.ai/)
