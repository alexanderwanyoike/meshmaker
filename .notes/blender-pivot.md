# CharMaker: Pivot to Blender Plugin

## Why Blender, Not Tauri

Blender already provides everything we were rebuilding in Tauri:
- 3D viewport, mesh editing, UV unwrapping
- Rigging and skinning tools (weight painting, bone editing)
- Animation timeline, NLA editor
- Import/export for GLB, FBX, OBJ
- Python scripting API (bpy) for calling RunPod backends
- Users can manually edit between pipeline stages

## Pipeline Models

| Stage | Model | Status |
|-------|-------|--------|
| 3D Generation | Trellis 2 | Deployed, working |
| 3D Generation | Hunyuan3D-2 | Planned |
| Part Segmentation | Hunyuan3D-Part (P3-SAM + X-Part) | Planned |
| Auto-Rigging | UniRig | Next to implement |
| Auto-Rigging | TokenRig/SkinTokens | Waiting on code release (arXiv 2602.04805) |
| Animation | HY-Motion | Container exists |

## What This Means

- `app/` (Tauri/React/TypeScript) is deprecated — no longer needed
- Backend containers stay exactly the same
- Frontend becomes a Blender addon that makes the same RunPod API calls
