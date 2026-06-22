# Card 02 - Fix the transport ceiling

Status: TODO
Depends on: 01 (asset-as-URL types)
Quality bar: Meshy-6 meshes (this is the prerequisite for it)

## Goal

Stop returning raw base64 assets in the RunPod JSON response. Handlers write output to object storage (S3 / Cloudflare R2) and return a URL; the client downloads from it. This is the single highest-leverage change in the project.

## Why

RunPod's synchronous response caps at ~20MB; base64 inflates bytes ~33%. To fit, every handler holds `texture_size=1024` and decimates aggressively, regardless of the model's true ceiling (`containers/trellis2/handler.py:116, 254`). The models have never been allowed to show their real quality. Fix this and existing models look dramatically better before any model swap.

## Scope

- Provision a bucket (R2 recommended: no egress fees). Add credentials to RunPod env + addon preferences.
- Add a small `upload_asset(bytes, key) -> url` helper used by every handler; return `{ "asset_url": ..., "metadata": ... }` instead of `{ "glb": "<base64>" }`.
- Update `meshmaker/api.py` to download from `asset_url` to a temp file before import.
- Use presigned URLs (time-limited) so the bucket isn't public.
- Apply across all output-producing handlers: trellis2, hunyuan3d, hunyuan3d-part, mia, hymotion.

## Acceptance criteria

- A Trellis2 generation at `texture_size=4096` round-trips successfully (would have blown the 20MB limit before).
- No handler returns base64 mesh/fbx payloads.
- Client import path works from a presigned URL.

## Notes

This unblocks card 04 (raise defaults). Order: 02 then 04.
