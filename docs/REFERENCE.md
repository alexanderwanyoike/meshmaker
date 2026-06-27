# MeshMaker - Reference

> The Generate (image -> mesh) landscape and the two provider API contracts MeshMaker ships against. Background for `cards/`, not a to-do list. Last refreshed June 2026.

## Active providers

| Provider | Model | Endpoint | Auth | GLB field |
|---|---|---|---|---|
| **Fal** | Hunyuan3D 3.1 Pro | `fal-ai/hunyuan-3d/v3.1/pro/image-to-3d` | `Authorization: Key <key>` | `model_glb.url` |
| **Meshy** | Image to 3D | `api.meshy.ai/openapi/v1/image-to-3d` | `Authorization: Bearer <key>` | `model_urls.glb` |

Both accept the reference image as a base64 data URI (`data:image/png;base64,...`),
so no separate image upload is required.

### Fal (queue API)

- **Submit:** `POST https://queue.fal.run/fal-ai/hunyuan-3d/v3.1/pro/image-to-3d`
  - body: `{ input_image_url, face_count (40k-1.5M, default 500k), enable_pbr, generate_type }`
  - returns: `{ request_id, status_url, response_url, cancel_url }`
- **Poll:** `GET <status_url>` -> `status` in `IN_QUEUE | IN_PROGRESS | COMPLETED`
- **Result:** `GET <response_url>` -> `{ model_glb: { url }, model_urls: { glb, obj, fbx, usdz }, thumbnail, seed }`
- **Cost:** ~$0.375/generation, +$0.15 with PBR. The `rapid` tier (`fal-ai/hunyuan-3d/v3.1/rapid/image-to-3d`) is the cheaper/faster swap.

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
| **Hunyuan3D 3.1** (active, via Fal) | Tencent | Commercial API | Current default. Strong geometry + PBR, hosted |
| **Meshy-5/6** (active) | Meshy | Commercial API | Textured, fast, good all-rounder |
| **Tripo / Prism 3.0** | VAST-AI | Commercial API | Closest Meshy competitor; has a Blender plugin |
| **Trellis 2** | Microsoft | MIT | Strong geometry, darker textures. Self-host only |
| **Hunyuan3D 2.1** | Tencent | Permissive | Good PBR. Self-host only |
| **TripoSG / TripoSR** | VAST-AI | MIT | Shape-only (SG) or very fast previews (SR) |

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
