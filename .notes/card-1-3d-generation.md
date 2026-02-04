# Card 1: 3D Generation Containers (Trellis 2 + Hunyuan 3D)

**Status:** Not Started
**Size:** Large (~4-5 days, can split if needed)
**Dependencies:** Card 0

---

## Goal

Image/text → GLB mesh generation on RunPod (both models).

---

## Research Needed

- [ ] Trellis 2 license (MIT?)
- [ ] Hunyuan 3D license
- [ ] VRAM requirements for each
- [ ] Docker base image selection

---

## Deliverables

- `containers/trellis2/Dockerfile`, `handler.py`
- `containers/hunyuan3d/Dockerfile`, `handler.py`
- Shared API schema (both return GLB)
- GitHub Actions for build/push

---

## API (same for both)

```json
{
  "input": {
    "image": "<base64 or URL>",  // OR
    "prompt": "a warrior character",
    "resolution": 512
  }
}
// Returns: GLB file (base64)
```

---

## Acceptance Criteria

- [ ] Both containers build successfully
- [ ] Both can generate GLB from image
- [ ] GLB outputs open in Blender/Unity
- [ ] Quality comparison documented

---

## Notes

- Supporting both models gives users options for quality vs speed tradeoffs
- May want to split this into two separate PRs if it gets too large
