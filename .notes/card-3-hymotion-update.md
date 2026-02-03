# Card 3: HY-Motion Container Update

**Status:** Not Started
**Size:** Medium (~2-3 days)
**Dependencies:** Card 0 (can be parallel with Cards 1, 2)

---

## Goal

Integrate Mixamo retargeting into existing container.

---

## Reference

- [hy-motion-fbx-exporter](https://github.com/zysilm-ai/hy-motion-fbx-exporter)
- [ComfyUI-HY-Motion1](https://github.com/jtydhr88/ComfyUI-HY-Motion1)

---

## Changes

- Add retargeting code from hy-motion-fbx-exporter
- Accept Mixamo FBX as input (the rigged character)
- Output animated FBX (not just NPZ)

---

## API

```json
{
  "input": {
    "prompt": "walking forward",
    "character_fbx": "<base64>",  // Mixamo-rigged FBX
    "duration": 4.0
  }
}
// Returns: Animated FBX (base64)
```

---

## Acceptance Criteria

- [ ] Can take UniRig output + prompt → animated FBX
- [ ] Animation plays correctly in Blender/Unity

---

## Notes

- This extends the existing hymotion container (currently in `cloud/`)
- Key integration point between rigging and animation
