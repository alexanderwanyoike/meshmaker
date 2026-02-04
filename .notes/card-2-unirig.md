# Card 2: UniRig RunPod Container

**Status:** Not Started
**Size:** Medium (~2-3 days)
**Dependencies:** Card 0 (can be parallel with Cards 1, 3)

---

## Goal

GLB mesh → Rigged FBX with Mixamo skeleton.

---

## Research Needed

- [ ] UniRig failure modes (what meshes don't work?)
- [ ] Output skeleton verification (is it truly Mixamo-compatible?)

---

## Deliverables

- `containers/unirig/Dockerfile`
- `containers/unirig/handler.py`
- Local test script

---

## API

```json
{
  "input": {
    "mesh": "<base64 GLB>",
    "format": "fbx"
  }
}
// Returns: Rigged FBX (base64)
```

---

## Acceptance Criteria

- [ ] Container builds successfully
- [ ] Can rig a Trellis 2 output
- [ ] FBX imports into Mixamo/Unity with correct skeleton

---

## Notes

- RunPod only for now (defer local option)
- Critical that output skeleton is Mixamo-compatible for HY-Motion integration
